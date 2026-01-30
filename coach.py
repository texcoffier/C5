# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes

"""
EFFICIENCY COACH FOR C5

Author: Tomas Delon Gago

This module implements a coaching system to help students
use keyboard shortcuts and efficient editing techniques.

Architecture:
    - CoachManager class: main manager that coordinates all coaches and manages shared state
    - Coach class: base class for individual coaches
    - Coach subclasses: each coach detects a specific inefficient pattern

Usage:
    coach = create_coach(options_dict)

    # In an event handler:
    # previous_position is optional; pass it if available
    result = coach.analyse(event, text, cursor_position, previous_position)
    if result:
        show_popup(result['message'])
        if 'restore_cursor_position' in result['actions']:
            restore_position(result['actions']['restore_cursor_position'])

Available coach options (configure in options.py, set to 0 to disable):

    - coach_tip_level: Enable/disable coaching system (0=disabled, 1=enabled)
    - coach_cooldown: Minimum delay between tips in milliseconds (default: 60000)

    - coach_mouse_short_move_distance: Max dx+dy distance in keystrokes for mouse tip (default: 3)

    - coach_mouse_line_bounds_min_move: Min chars moved for Home/End tip (default: 2)

    - coach_many_horizontal_arrows_threshold: Consecutive ←/→ before tip (default: 20)

    - coach_many_vertical_arrows_threshold: Consecutive ↑/↓ before tip (default: 50)

    - coach_arrow_then_backspace_count: →+Backspace repetitions before tip (default: 3)

    - coach_retype_after_delete_chars: Min retyped chars for undo tip (default: 10)

    - coach_scroll_full_document_edge_lines: Lines from edge for scroll tip (default: 3)
    - coach_scroll_full_document_min_lines: Min file lines for scroll tip (default: 200)

    - coach_letter_select_word_threshold: Shift+arrows before select tip (default: 20)

    - coach_delete_word_char_by_char_threshold: Backspace/Delete before tip (default: 20)

    - coach_copy_then_delete_max_delay: Max ms between Ctrl+C and Delete (default: 3000)
"""

# ════════════════════════════════════════════════════════════════════════════
# COACHING TIP MESSAGES (in French for students)
# ════════════════════════════════════════════════════════════════════════════

COACH_MESSAGES = {
    'mouse_short_move': (
        "🐢 Trop lent avec la souris !<br><br>"
        + "Pour de petits déplacements, vos doigts sont plus rapides que votre main :<br>"
        + "Utilisez <kbd>←</kbd> <kbd>→</kbd> ou <kbd>↑</kbd> <kbd>↓</kbd> au lieu de la souris.<br>"
        + "<em>Astuce pro : gardez vos mains sur le clavier ! 🎮</em>"
    ),
    'mouse_line_bounds': (
        "🎯 Vous visez le début ou la fin de ligne ?<br><br>"
        + "Arrêtez de cliquer comme un pigeon ! 🐦<br>"
        + "Utilisez <kbd>↖</kbd> (<i>Home</i>) pour le début, "
        + "<kbd>Fin</kbd> (<i>End</i>) pour la fin.<br>"
        + "Sur portable : <kbd>Fn</kbd> + <kbd>←</kbd> ou <kbd>Fn</kbd> + <kbd>→</kbd>"
    ),
    'many_horizontal_arrows': (
        "⌨️ Wow, vous aimez vraiment cette touche fléchée !<br><br>"
        + "Pour aller plus vite :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>←</kbd> / <kbd>Ctrl</kbd> + <kbd>→</kbd> = sauter de mot en mot 🦘<br>"
        + "• <kbd>↖</kbd> (<i>Home</i>)/<kbd>Fin</kbd> (<i>End</i>) = début/fin de ligne ⚡<br>"
        + "<em>Vos doigts vous remercieront !</em>"
    ),
    'many_vertical_arrows': (
        "🏃 Marathon de touches fléchées détecté !<br><br>"
        + "Vous descendez l'Everest ligne par ligne ? 🏔️<br>"
        + "• <kbd>⇞</kbd> (<i>PageUp</i>) / <kbd>⇟</kbd> (<i>PageDown</i>) = sauter de page en page<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>↖</kbd> / <kbd>Ctrl</kbd> + <kbd>Fin</kbd> = début/fin du fichier<br>"
        + "<em>C'est comme un ascenseur pour votre code ! 🛗</em>"
    ),
    'arrow_then_backspace': (
        "🤔 Hmm, vous faites compliqué là...<br><br>"
        + "Au lieu de <kbd>→</kbd> puis <kbd>⌫</kbd> (<i>backspace</i>), utilisez simplement "
        + "<kbd>Suppr</kbd> !<br>"
        + "C'est 2 touches → 1 touche. Même votre calculatrice approuverait. 🧮<br>"
        + "<em>Travaillez plus intelligemment, pas plus dur !</em>"
    ),
    'retype_after_delete': (
        "😱 STOP ! Vous retapez ce que vous venez d'effacer !<br><br>"
        + "C'est comme creuser un trou pour le reboucher... 🕳️⛏️<br>"
        + "Utilisez plutôt :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Z</kbd> pour annuler<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Y</kbd> pour rétablir<br>"
        + "<em>Vos doigts ne sont pas un time machine, mais Ctrl+Z oui ! ⏰✨</em>"
    ),
    'scroll_full_document': (
        "🚀 Vous avez atteint le bout du monde !<br><br>"
        + "Pour aller directement au début ou à la fin du fichier :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>↖</kbd> = début du fichier ⬆️<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Fin</kbd> = fin du fichier ⬇️<br>"
        + "<em>Téléportation instantanée ! ✨</em>"
    ),
    'letter_select_word': (
        "🔤 Sélectionner lettre par lettre ? Vraiment ?<br><br>"
        + "Pour sélectionner un mot entier :<br>"
        + "• Double-clic sur le mot 🖱️<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>←</kbd> / <kbd>→</kbd> = mot par mot<br>"
        + "<em>Travaillez plus intelligemment ! 🧠</em>"
    ),
    'delete_word_char_by_char': (
        "⌫ Vous effacez un mot entier caractère par caractère ?<br><br>"
        + "Pour supprimer un mot complet d'un coup :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>⌫</kbd> (<i>backspace</i>) = supprimer mot à gauche ⬅️<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>Suppr</kbd> = supprimer mot à droite ➡️<br>"
        + "<em>Un mot = une touche ! 💥</em>"
    ),
    'copy_then_delete': (
        "✂️ Copier puis supprimer ? Il y a plus simple !<br><br>"
        + "Au lieu de <kbd>Ctrl</kbd> + <kbd>C</kbd> puis "
        + "<kbd>Suppr</kbd>, utilisez directement :<br>"
        + "• <kbd>Ctrl</kbd> + <kbd>X</kbd> = couper (copie + supprime) ✂️<br>"
        + "<em>Deux touches → une touche ! 🚀</em>"
    )
}

# ════════════════════════════════════════════════════════════════════════════
# AUXILIARY FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def get_line_column(text, position):
    """Returns (line, column) from absolute position. Line is 1-indexed, column is 0-indexed."""
    lines = text[:position].split('\n')
    line_number = len(lines)
    column = len(lines[-1])
    return line_number, column

def prefix_length(text1, text2):
    if text1 == text2:
        return len(text1)
    i = 0
    for a, b in zip(text1, text2):
        if a != b:
            return i
        i += 1
    return i

# ════════════════════════════════════════════════════════════════════════════
# COACH MANAGER CLASS
# ════════════════════════════════════════════════════════════════════════════

class CoachManager:
    """Manages all coaching instances and shared state."""

    def __init__(self, coaches, options):
        self.coaches = coaches
        self.options = options or {}
        self.last_event_type = None
        self.previous_position = 0
        self.last_popup = {}
        self.now = 0
        self.popup_cooldown = self.get_option('coach_cooldown', 60000)
        self.coach_tip_level = self.get_option('coach_tip_level')

        for coach in self.coaches:
            coach.manager = self
            for option_name in coach.parameters:
                default_value = coach.parameters[option_name]
                short_name = option_name.replace(coach.option + '_', '')
                setattr(coach, short_name, self.get_option(option_name, default_value))
            coach.enabled = getattr(coach, coach.enable_param, 0) > 0

    def should_check(self, coach, event):
        """Returns True if the coach is enabled and must receive the event."""
        if not self.coach_tip_level:
            return False
        if not coach.enabled:
            return False
        if coach.expected_event_type == '*':
            return True
        return coach.expected_event_type == event.type

    def get_key_info(self, event):
        """Returns (key, ctrl, shift) from keyboard event."""
        if not event:
            return None, False, False
        key = event.key
        ctrl = bool(event.ctrlKey)
        shift = bool(event.shiftKey)
        return key, ctrl, shift

    def get_option(self, option, by_default=0):
        """Gets an option value, returning by_default if not set."""
        value = self.options[option]
        if eval('isNaN(value)') or value == '':  # pylint: disable=eval-used
            value = by_default
        return int(value)

    def analyse(self, event, text, cursor_position, previous_position=None):
        """Checks all coaches and returns first tip detected, or None."""
        if previous_position is not None:
            self.previous_position = previous_position

        self.now = eval('Date.now()') # pylint: disable=eval-used

        current_event_type = None
        if event:
            current_event_type = event.type

        for coach in self.coaches:
            if self.should_check(coach, event):
                result = coach.check(event, text, cursor_position)
                if result:
                    self.last_event_type = current_event_type
                    return result

        self.last_event_type = current_event_type
        return None


# ════════════════════════════════════════════════════════════════════════════
# BASE COACH CLASS
# ════════════════════════════════════════════════════════════════════════════

class Coach:
    """Base class for individual coaches. Subclasses override check() method."""

    option = None
    expected_event_type = None
    parameters = {}

    def __init__(self):
        pass

    def tip_activable(self, actions=None):
        """Returns tip dict if cooldown elapsed, None otherwise."""
        if self.option in self.manager.last_popup:
            last = self.manager.last_popup[self.option]
        else:
            last = 0

        if self.manager.now - last < self.manager.popup_cooldown:
            return None

        self.manager.last_popup[self.option] = self.manager.now
        message_key = self.option.replace('coach_', '')
        return {'option': self.option, 'message': COACH_MESSAGES[message_key], 'actions': actions or {}}

    def check(self, event, text, cursor_position):
        """Override in subclasses to implement detection logic."""
        pass


# ════════════════════════════════════════════════════════════════════════════
# KEY STREAK COACH BASE CLASS
# ════════════════════════════════════════════════════════════════════════════

class KeyStreakCoach(Coach):
    """
    Base class for coaches that detect N consecutive identical keystrokes.
    Subclasses define valid_keys and threshold (via parameters).
    """
    valid_keys = []
    allow_ctrl = False
    allow_shift = False
    require_shift = False
    track_direction = True
    expected_event_type = 'keydown'

    def __init__(self):
        self.streak = 0
        self.last_direction = None

    def reset_streak(self):
        self.streak = 0
        self.last_direction = None

    def modifier_forbidden(self, ctrl, shift):
        if ctrl and not self.allow_ctrl:
            return True
        if shift and not self.allow_shift and not self.require_shift:
            return True
        return False

    def check(self, event, text, cursor_position):
        key, ctrl, shift = self.manager.get_key_info(event)
        if not key:
            return None

        if self.require_shift and not shift:
            self.reset_streak()
            return None

        if self.modifier_forbidden(ctrl, shift):
            self.reset_streak()
            return None

        if key not in self.valid_keys:
            self.reset_streak()
            return None

        if self.track_direction and self.last_direction and key != self.last_direction:
            self.streak = 0

        self.last_direction = key
        self.streak += 1

        if self.streak >= self.threshold:
            result = self.tip_activable()
            if result:
                self.streak = 0
            return result

        return None


# ════════════════════════════════════════════════════════════════════════════
# SPECIFIC COACHES - INEFFICIENT PATTERN DETECTION
# ════════════════════════════════════════════════════════════════════════════

class MouseCoach(Coach):
    """Base class for mouse movement detection. Subclasses implement check_movement()."""
    min_click_delay = 300
    expected_event_type = 'mouseup'

    def __init__(self):
        self.last_event_time = 0

    def check(self, event, text, cursor_position):
        if self.manager.last_event_type == 'mouseup':
            return None

        idle = self.manager.now - self.last_event_time
        self.last_event_time = self.manager.now
        if idle < self.min_click_delay:
            return None

        previous_position = self.manager.previous_position or 0
        prev_line, prev_col = get_line_column(text, previous_position)
        new_line, new_col = get_line_column(text, cursor_position)

        return self.check_movement(prev_line, prev_col, new_line, new_col, text)

    def check_movement(self, prev_line, prev_col, new_line, new_col, text):
        pass


class Mouse_short_move(MouseCoach):
    """Detects small mouse movements that could be done with arrow keys."""
    option = 'coach_mouse_short_move'
    enable_param = 'distance'
    parameters = {
        'coach_mouse_short_move_distance': 3
    }

    def check_movement(self, prev_line, prev_col, new_line, new_col, text):
        dy = abs(new_line - prev_line)
        dx = abs(new_col - prev_col)

        if dx + dy == 0:
            return None

        if dx + dy <= self.distance:
            return self.tip_activable()

        return None


class Mouse_line_bounds(MouseCoach):
    """Detects mouse click to line beginning/end (suggests Home/End keys)."""
    option = 'coach_mouse_line_bounds'
    enable_param = 'min_move'
    parameters = {
        'coach_mouse_line_bounds_min_move': 2
    }

    def check_movement(self, prev_line, prev_col, new_line, new_col, text):
        if prev_line != new_line:
            return None

        if abs(new_col - prev_col) < self.min_move:
            return None

        lines = text.split('\n')
        if new_line >= 1 and new_line <= len(lines):
            line_length = len(lines[new_line - 1])
            if new_col == 0 or new_col == line_length:
                return self.tip_activable()

        return None


class Many_horizontal_arrows(KeyStreakCoach):
    """Detects many consecutive ← → arrows (suggests Ctrl+arrows or Home/End)."""
    option = 'coach_many_horizontal_arrows'
    valid_keys = ['ArrowLeft', 'ArrowRight']
    enable_param = 'threshold'
    parameters = {
        'coach_many_horizontal_arrows_threshold': 20
    }


class Many_vertical_arrows(KeyStreakCoach):
    """Detects many consecutive ↑ ↓ arrows (suggests PageUp/PageDown)."""
    option = 'coach_many_vertical_arrows'
    valid_keys = ['ArrowUp', 'ArrowDown']
    enable_param = 'threshold'
    parameters = {
        'coach_many_vertical_arrows_threshold': 50
    }


class KeySequenceCoach(Coach):
    """Base class for detecting key A followed by key B within a time limit."""
    first_key = None
    first_ctrl = False
    second_keys = []
    second_ctrl = False
    max_delay = 2000
    repeat_count = 0
    expected_event_type = 'keydown'

    def __init__(self):
        self.first_timestamp = 0
        self.streak = 0

    def check(self, event, text, cursor_position):
        key, ctrl, _ = self.manager.get_key_info(event)
        if not key:
            return None

        if key == self.first_key and ctrl == self.first_ctrl:
            self.first_timestamp = self.manager.now
            return None

        if key in self.second_keys and ctrl == self.second_ctrl:
            if self.first_timestamp > 0 and (self.manager.now - self.first_timestamp) < self.max_delay:
                self.streak += 1
                if self.repeat_count == 0 or self.streak >= self.repeat_count:
                    result = self.tip_activable()
                    if result:
                        self.first_timestamp = 0
                        self.streak = 0
                        return result
                self.first_timestamp = 0
            else:
                self.streak = 0
            return None

        self.first_timestamp = 0
        self.streak = 0
        return None


class Arrow_then_backspace(KeySequenceCoach):
    """Detects repeated → then Backspace (suggests Delete key)."""
    option = 'coach_arrow_then_backspace'
    enable_param = 'count'
    first_key = 'ArrowRight'
    second_keys = ['Backspace']
    parameters = {
        'coach_arrow_then_backspace_count': 3
    }

    def __init__(self):
        KeySequenceCoach.__init__(self)

    def check(self, event, text, cursor_position):
        self.repeat_count = self.count
        return KeySequenceCoach.check(self, event, text, cursor_position)


class Retype_after_delete(Coach):
    """Detects retyping deleted text (suggests Ctrl+Z to undo)."""
    option = 'coach_retype_after_delete'
    max_delay_ms = 10000
    deletion_merge_delay = 2000
    expected_event_type = '*'
    enable_param = 'chars'
    parameters = {
        'coach_retype_after_delete_chars': 10
    }

    def __init__(self):
        self.previous_text = ''
        self.deleted_buffer = ''
        self.deletion_time = 0
        self.text_after_deletion = ''

    def reset_detection(self):
        self.deletion_time = 0
        self.deleted_buffer = ''

    def check(self, event, text, cursor_position):
        if len(text) < len(self.previous_text):
            deleted_length = len(self.previous_text) - len(text)
            deleted_position = prefix_length(text, self.previous_text)
            deleted_text = self.previous_text[deleted_position:deleted_position + deleted_length]

            is_recent_deletion = (self.manager.now - self.deletion_time) < self.deletion_merge_delay
            if is_recent_deletion and len(self.deleted_buffer) > 0:
                if deleted_position == len(text):
                    self.deleted_buffer = self.deleted_buffer + deleted_text
                else:
                    self.deleted_buffer = deleted_text + self.deleted_buffer
            else:
                self.deleted_buffer = deleted_text

            self.text_after_deletion = text
            self.deletion_time = self.manager.now

        elif len(text) > len(self.previous_text):
            is_within_window = (self.manager.now - self.deletion_time) < self.max_delay_ms
            if is_within_window and len(self.deleted_buffer) >= 3:
                retyped_text = ''
                if len(text) > len(self.text_after_deletion):
                    added_length = len(text) - len(self.text_after_deletion)
                    added_position = prefix_length(self.text_after_deletion, text)
                    retyped_text = text[added_position:added_position + added_length]

                chars_added = len(text) - len(self.previous_text)
                match_length = prefix_length(retyped_text, self.deleted_buffer)

                if chars_added >= 5:
                    self.reset_detection()
                elif match_length >= self.chars - 1 and match_length > 0:
                    result = self.tip_activable()
                    if result:
                        self.reset_detection()
                        self.previous_text = text
                        return result

        self.previous_text = text
        return None


class Scroll_full_document(Coach):
    """Detects scroll from top to bottom of document (suggests Ctrl+Home/End)."""
    option = 'coach_scroll_full_document'
    expected_event_type = '*'
    enable_param = 'min_lines'
    parameters = {
        'coach_scroll_full_document_edge_lines': 3,
        'coach_scroll_full_document_min_lines': 200
    }

    def __init__(self):
        self.previous_zone = None

    def check(self, _event, text, cursor_position):
        current_line, _ = get_line_column(text, cursor_position)
        total_lines = len(text.split('\n'))

        if total_lines < self.min_lines:
            return None

        at_top = current_line <= self.edge_lines
        at_bottom = current_line > total_lines - self.edge_lines

        if at_top:
            current_zone = 'top'
        elif at_bottom:
            current_zone = 'bottom'
        else:
            current_zone = 'middle'

        if self.previous_zone and current_zone != self.previous_zone:
            if (self.previous_zone == 'top' and current_zone == 'bottom') or \
               (self.previous_zone == 'bottom' and current_zone == 'top'):
                result = self.tip_activable()
                if result:
                    self.previous_zone = current_zone
                    return result

        self.previous_zone = current_zone

        return None


class Letter_select_word(KeyStreakCoach):
    """Detects selecting word char by char (suggests double-click or Ctrl+Shift+arrows)."""
    option = 'coach_letter_select_word'
    valid_keys = ['ArrowLeft', 'ArrowRight']
    require_shift = True
    allow_ctrl = False
    enable_param = 'threshold'
    parameters = {
        'coach_letter_select_word_threshold': 20
    }


class Delete_word_char_by_char(KeyStreakCoach):
    """Detects deleting word char by char (suggests Ctrl+Backspace/Delete)."""
    option = 'coach_delete_word_char_by_char'
    valid_keys = ['Backspace', 'Delete']
    track_direction = False
    enable_param = 'threshold'
    parameters = {
        'coach_delete_word_char_by_char_threshold': 20
    }


class Copy_then_delete(KeySequenceCoach):
    """Detects Ctrl+C then Delete/Backspace (suggests Ctrl+X to cut)."""
    option = 'coach_copy_then_delete'
    enable_param = 'max_delay'
    first_key = 'c'
    first_ctrl = True
    second_keys = ['Delete', 'Backspace']
    parameters = {
        'coach_copy_then_delete_max_delay': 3000
    }

    def __init__(self):
        KeySequenceCoach.__init__(self)

    def check(self, event, text, cursor_position):
        self.max_delay = getattr(self, 'max_delay', 3000)
        return KeySequenceCoach.check(self, event, text, cursor_position)


def create_coach(options):
    manager = CoachManager(
        [
        Mouse_short_move(),
        Mouse_line_bounds(),
        Many_horizontal_arrows(),
        Many_vertical_arrows(),
        Arrow_then_backspace(),
        Retype_after_delete(),
        Scroll_full_document(),
        Letter_select_word(),
        Delete_word_char_by_char(),
        Copy_then_delete()
        ],
        options
    )
    if manager.coach_tip_level:
        return manager
    # Coach not activated.

