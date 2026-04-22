import pygame
from utils import get_ui_image, clamp, lerp


WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
NEAR_BLACK = (10,  10,  10)
DARK_GRAY  = (40,  40,  40)
MID_GRAY   = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)


# ─────────────────────────────────────────────────────────────────────────────
# Item definitions
# Each item has an "effect" dict:
#   {"stat": NAME, "delta": N}          → applied once to patient at session start
#   {"special": KEY}                    → added to active_effects set
#   {"turns": KEY, "count": N}          → added to turn_effects dict for N turns
# ─────────────────────────────────────────────────────────────────────────────
ITEMS = [
    # ── Existing favourites (revised descriptions) ────────────────────────────
    {
        "id":          "case_file",
        "name":        "Case File",
        "description": "Reveals the patient's illness before the session starts. Helps with the illness quiz.",
        "effect":      {"special": "reveal_illness"},
        "price":       18,
        "icon":        "case_file",
        "stock":       3,
    },
    {
        "id":          "extra_heart",
        "name":        "Extra Heart",
        "description": "Restores 1 lost heart immediately.",
        "effect":      {"special": "restore_heart"},
        "price":       40,
        "icon":        "extra_heart",
        "stock":       2,
    },
    {
        "id":          "coffee",
        "name":        "Coffee",
        "description": "Reduces patient Exhaustion by 20 at the start of the session.",
        "effect":      {"stat": "Exhaustion", "delta": -20},
        "price":       10,
        "icon":        "coffee",
        "stock":       3,
    },

    # ── New session boosts ────────────────────────────────────────────────────
    {
        "id":          "calming_tea",
        "name":        "Calming Tea",
        "description": "Session boost: all negative stat changes are halved for the entire session.",
        "effect":      {"special": "slow_drain"},
        "price":       22,
        "icon":        "calming_tea",
        "stock":       2,
    },
    {
        "id":          "empathy_boost",
        "name":        "Empathy Boost",
        "description": "Turn boost: for the next 10 turns every positive stat gain is doubled.",
        "effect":      {"turns": "empathy_boost", "count": 10},
        "price":       28,
        "icon":        "stress_ball",   # reuse icon until a custom one exists
        "stock":       2,
    },
    {
        "id":          "focus_notes",
        "name":        "Focus Notes",
        "description": "Turn boost: for the next 15 turns every good choice gives +2 bonus to each positive stat.",
        "effect":      {"turns": "focus_notes", "count": 15},
        "price":       20,
        "icon":        "case_file",     # reuse icon
        "stock":       2,
    },

    # ── Debuff / utility ──────────────────────────────────────────────────────
    {
        "id":          "cleanser",
        "name":        "Cleanser",
        "description": "Removes the Weakness debuff immediately. Also restores 5 Calm to the patient.",
        "effect":      {"special": "cleanse_weakness"},
        "price":       30,
        "icon":        "calming_tea",   # reuse icon
        "stock":       2,
    },
    {
        "id":          "stress_ball",
        "name":        "Stress Ball",
        "description": "The next stat warning this session is completely ignored.",
        "effect":      {"special": "ignore_warning"},
        "price":       14,
        "icon":        "stress_ball",
        "stock":       3,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Shop
# ─────────────────────────────────────────────────────────────────────────────
class Shop:
    def __init__(self):
        self.inventory      = [dict(item) for item in ITEMS]
        self.coins          = 0
        self.active_effects = set()
        # turn_effects: {key: turns_remaining}
        self.turn_effects   = {}

    # ── Economy ───────────────────────────────────────────────────────────────

    def earn_coins(self, amount):
        self.coins = max(0, self.coins + amount)
        print(f"[Shop] coins {'+'if amount>=0 else ''}{amount} → {self.coins}")

    def can_afford(self, item_id):
        item = self._get_item(item_id)
        return item is not None and self.coins >= item["price"] and item["stock"] > 0

    def buy(self, item_id):
        if not self.can_afford(item_id):
            return False
        item = self._get_item(item_id)
        self.coins    -= item["price"]
        item["stock"] -= 1

        effect = item.get("effect", {})
        if "special" in effect:
            self.active_effects.add(effect["special"])
        elif "turns" in effect:
            key   = effect["turns"]
            count = effect.get("count", 10)
            self.turn_effects[key] = self.turn_effects.get(key, 0) + count

        print(f"[Shop] Bought {item['name']}. coins={self.coins} stock={item['stock']}")
        return True

    # ── Effect helpers ────────────────────────────────────────────────────────

    def has_effect(self, effect_name):
        return effect_name in self.active_effects

    def consume_effect(self, effect_name):
        self.active_effects.discard(effect_name)

    def get_turn_effect(self, key):
        """Returns remaining turns for a turn-based effect (0 if inactive)."""
        return self.turn_effects.get(key, 0)

    def consume_turn_effect(self, key):
        """Decrement a turn effect by 1. Removes when it hits 0."""
        if key in self.turn_effects:
            self.turn_effects[key] -= 1
            if self.turn_effects[key] <= 0:
                del self.turn_effects[key]

    def reset_session_effects(self):
        """Clear all session-scoped effects at end of session."""
        session_effects = {"ignore_warning", "slow_drain", "reveal_illness"}
        self.active_effects -= session_effects
        # Turn effects also expire between sessions
        self.turn_effects.clear()

    def use_stat_item(self, item_id, patient):
        item = self._get_item(item_id)
        if item is None:
            return
        effect = item.get("effect", {})
        if "stat" in effect:
            patient.update_stat(effect["stat"], effect["delta"])

    def _get_item(self, item_id):
        for item in self.inventory:
            if item["id"] == item_id:
                return item
        return None

    def get_inventory(self):
        return self.inventory


# ─────────────────────────────────────────────────────────────────────────────
# ShopUI
# ─────────────────────────────────────────────────────────────────────────────
class ShopUI:
    ICON_SIZE   = 80
    ICON_GAP    = 14
    PANEL_W     = 480
    PANEL_H     = 420
    RIGHT_W     = 200
    SLIDE_SPEED = 800

    def __init__(self, screen_w, screen_h, font_small, font_medium, font_large):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.font_s   = font_small
        self.font_m   = font_medium
        self.font_l   = font_large

        self.visible        = False
        self.selected_index = -1
        self._right_open    = False

        px = screen_w // 2 - self.PANEL_W // 2
        py = screen_h // 2 - self.PANEL_H // 2
        self.base_rect  = pygame.Rect(px, py, self.PANEL_W, self.PANEL_H)
        self.panel_rect = pygame.Rect(px, py, self.PANEL_W, self.PANEL_H)
        self.right_rect = pygame.Rect(px + self.PANEL_W, py, self.RIGHT_W, self.PANEL_H)

        self.icon_rects = []
        self._build_icon_rects()

        self.buy_btn = pygame.Rect(0, 0, 120, 38)

        self.overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 140))

        self._icons = {}

    def _build_icon_rects(self):
        self.icon_rects = []
        cols    = 3
        start_x = self.panel_rect.x + 30
        start_y = self.panel_rect.y + 80
        for i in range(len(ITEMS)):
            col = i % cols
            row = i // cols
            x   = start_x + col * (self.ICON_SIZE + self.ICON_GAP)
            y   = start_y + row * (self.ICON_SIZE + self.ICON_GAP)
            self.icon_rects.append(pygame.Rect(x, y, self.ICON_SIZE, self.ICON_SIZE))

    def toggle(self):
        self.visible = not self.visible
        if not self.visible:
            self.selected_index = -1
            self._right_open    = False

    def handle_event(self, event, shop, game):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            total_rect = (self.panel_rect.union(self.right_rect)
                          if self._right_open else self.panel_rect)
            if not total_rect.collidepoint(event.pos):
                self.toggle()
                return True

            for i, rect in enumerate(self.icon_rects):
                if rect.collidepoint(event.pos):
                    game.play_sound("click")
                    if self.selected_index == i:
                        self.selected_index = -1
                        self._right_open    = False
                    else:
                        self.selected_index = i
                        self._right_open    = True
                    return True

            if self._right_open and self.buy_btn.collidepoint(event.pos):
                if self.selected_index >= 0:
                    item_id = ITEMS[self.selected_index]["id"]
                    if shop.buy(item_id):
                        game.play_sound("click")
                        # Immediate special effects
                        if item_id == "extra_heart":
                            from game import MAX_HEARTS
                            game.hearts = min(game.hearts + 1, MAX_HEARTS)
                            shop.consume_effect("restore_heart")
                        elif item_id == "cleanser":
                            game.weakness_active = False
                            shop.consume_effect("cleanse_weakness")
                            # Also apply the Calm boost to current patient if in session
                            if game.current_session and game.current_session.patient:
                                game.current_session.patient.update_stat("Calm", 5)
                        # Turn-based effects: push counts into DialogueManager
                        if game.current_session and game.current_session.dialogue_mgr:
                            dm = game.current_session.dialogue_mgr
                            dm.focus_turns_left   = shop.get_turn_effect("focus_notes")
                            dm.empathy_turns_left = shop.get_turn_effect("empathy_boost")
                    else:
                        game.play_sound("warning")
                return True

        return True

    def update(self, dt):
        if not self.visible:
            return
        target_offset  = self.RIGHT_W if self._right_open else 0
        current_offset = self.right_rect.x - (self.base_rect.x + self.PANEL_W)
        new_offset     = lerp(current_offset, target_offset,
                              min(1.0, self.SLIDE_SPEED * dt / self.RIGHT_W))
        self.right_rect.x = self.base_rect.x + self.PANEL_W + int(new_offset)
        shift = int(new_offset * 0.4)
        self.panel_rect.x = self.base_rect.x - shift
        self._build_icon_rects()

    def draw(self, surface, shop):
        if not self.visible:
            return

        surface.blit(self.overlay, (0, 0))

        pygame.draw.rect(surface, NEAR_BLACK, self.panel_rect, border_radius=10)
        pygame.draw.rect(surface, WHITE,      self.panel_rect, 2, border_radius=10)

        title = self.font_l.render("Shop", True, WHITE)
        surface.blit(title, (self.panel_rect.centerx - title.get_width() // 2,
                              self.panel_rect.y + 14))

        coins_surf = self.font_m.render(f"Coins: {shop.coins}", True, LIGHT_GRAY)
        surface.blit(coins_surf, (self.panel_rect.right - coins_surf.get_width() - 16,
                                   self.panel_rect.y + 18))

        # Active turn effects summary
        te_lines = []
        if shop.get_turn_effect("focus_notes") > 0:
            te_lines.append(f"Focus: {shop.get_turn_effect('focus_notes')} turns")
        if shop.get_turn_effect("empathy_boost") > 0:
            te_lines.append(f"Empathy: {shop.get_turn_effect('empathy_boost')} turns")
        for idx, line in enumerate(te_lines):
            s = self.font_s.render(line, True, (220, 180, 60))
            surface.blit(s, (self.panel_rect.x + 16,
                             self.panel_rect.y + 52 + idx * 18))

        for i, (item, rect) in enumerate(zip(shop.inventory, self.icon_rects)):
            self._draw_item_icon(surface, item, rect, i, shop)

        if self._right_open and self.selected_index >= 0:
            self._draw_info_panel(surface, shop)

    def _draw_item_icon(self, surface, item, rect, index, shop):
        selected     = index == self.selected_index
        out_of_stock = item["stock"] <= 0

        bg = DARK_GRAY if not selected else (60, 60, 60)
        pygame.draw.rect(surface, bg, rect, border_radius=8)
        border_color = WHITE if selected else MID_GRAY
        pygame.draw.rect(surface, border_color, rect,
                         2 if selected else 1, border_radius=8)

        icon = self._get_icon(item["icon"])
        if icon:
            icon_scaled = pygame.transform.scale(
                icon, (self.ICON_SIZE - 16, self.ICON_SIZE - 16))
            surface.blit(icon_scaled, (rect.x + 8, rect.y + 8))
        else:
            t = self.font_s.render(item["name"][:6], True, LIGHT_GRAY)
            surface.blit(t, (rect.centerx - t.get_width()  // 2,
                             rect.centery - t.get_height() // 2))

        stock_color = MID_GRAY if out_of_stock else LIGHT_GRAY
        stock_surf  = self.font_s.render(f"x{item['stock']}", True, stock_color)
        surface.blit(stock_surf, (rect.right - stock_surf.get_width() - 4,
                                   rect.bottom - stock_surf.get_height() - 4))

        price_surf = self.font_s.render(f"{item['price']}c", True, LIGHT_GRAY)
        surface.blit(price_surf, (rect.x + 4, rect.bottom - price_surf.get_height() - 4))

        if out_of_stock:
            dim = pygame.Surface(rect.size, pygame.SRCALPHA)
            dim.fill((0, 0, 0, 120))
            surface.blit(dim, rect.topleft)

    def _draw_info_panel(self, surface, shop):
        item     = ITEMS[self.selected_index]
        inv_item = shop._get_item(item["id"])
        rect     = self.right_rect

        pygame.draw.rect(surface, DARK_GRAY, rect, border_radius=10)
        pygame.draw.rect(surface, WHITE,     rect, 2,  border_radius=10)

        y = rect.y + 16
        name_surf = self.font_m.render(item["name"], True, WHITE)
        surface.blit(name_surf, (rect.centerx - name_surf.get_width() // 2, y))
        y += name_surf.get_height() + 10

        pygame.draw.line(surface, MID_GRAY,
                         (rect.x + 10, y), (rect.right - 10, y), 1)
        y += 10

        # Wrapped description
        desc_words = item["description"].split()
        line       = ""
        for word in desc_words:
            test = line + (" " if line else "") + word
            if self.font_s.size(test)[0] <= rect.width - 20:
                line = test
            else:
                if line:
                    t = self.font_s.render(line, True, LIGHT_GRAY)
                    surface.blit(t, (rect.x + 10, y))
                    y += t.get_height() + 4
                line = word
        if line:
            t = self.font_s.render(line, True, LIGHT_GRAY)
            surface.blit(t, (rect.x + 10, y))
            y += t.get_height() + 12

        price_surf = self.font_m.render(f"{item['price']} coins", True, LIGHT_GRAY)
        surface.blit(price_surf, (rect.centerx - price_surf.get_width() // 2, y))
        y += price_surf.get_height() + 10

        can_buy   = shop.can_afford(item["id"])
        btn_color = DARK_GRAY if not can_buy else (60, 60, 60)
        btn_fg    = MID_GRAY  if not can_buy else WHITE
        self.buy_btn = pygame.Rect(rect.centerx - 60, rect.bottom - 54, 120, 38)
        pygame.draw.rect(surface, btn_color, self.buy_btn, border_radius=6)
        pygame.draw.rect(surface, WHITE if can_buy else MID_GRAY,
                         self.buy_btn, 1, border_radius=6)
        buy_label = self.font_m.render("Buy", True, btn_fg)
        surface.blit(buy_label,
                     (self.buy_btn.centerx - buy_label.get_width()  // 2,
                      self.buy_btn.centery - buy_label.get_height() // 2))

        stock_surf = self.font_s.render(
            f"Stock: {inv_item['stock']}", True, MID_GRAY)
        surface.blit(stock_surf,
                     (rect.centerx - stock_surf.get_width() // 2,
                      self.buy_btn.bottom + 6))

    def _get_icon(self, icon_name):
        if icon_name in self._icons:
            return self._icons[icon_name]
        try:
            surf = pygame.image.load(
                f"Soft Hours/assets/images/ui/items/{icon_name}.png"
            ).convert_alpha()
            self._icons[icon_name] = surf
        except FileNotFoundError:
            self._icons[icon_name] = None
        return self._icons[icon_name]