/**
 * Two-key hotkey combo map. Shift must be held for both keys.
 * Format: { [firstKey]: { [secondKey]: labelName } }
 *
 * Keys are the `event.key` values when Shift is held.
 */
export const HOTKEY_COMBOS: Record<string, Record<string, string>> = {
  D: {
    D: 'Drive',
    T: 'Defenders Double Team',
    S: 'Defenders Switch',
    F: 'Deflection',
    U: 'Ballhandler Defender Under Screen',
    O: 'Ballhandler Defender Over Screen',
    B: 'Dead Ball Turnover',
    R: 'Defensive Rebound',
    G: 'Defensive Goaltending',
  },
  H: {
    O: 'Handoff',
  },
  O: {
    B: 'On Ball Screen',
    S: 'Off Ball Screen',
    F: 'Offensive Foul',
    O: 'Out of Bounds',
    R: 'Offensive Rebound',
  },
  F: {
    H: 'Fake Handoff',
    T: 'FT Attempt',
  },
  P: {
    U: 'Post Up',
    S: 'Pass Attempt',
    R: 'Pass Received',
  },
  S: {
    R: 'Screener Rolling to Rim',
    P: 'Screener Popping',
    G: 'Screener Ghosting',
    S: 'Screener Slipping the Screen',
    T: 'Steal',
    F: 'Shooting Foul',
    D: 'Screener Defender Dropping',
    L: 'Screener Defender at the Level',
    H: 'Screener Defender Hedging',
  },
  T: {
    S: 'Transition',
  },
  I: {
    S: 'Isolation',
    P: 'Inbound Pass',
  },
  C: {
    T: 'Cut',
    F: 'Non-shooting Foul',
  },
  B: {
    S: 'Blocked Shot',
  },
  R: {
    S: 'Ballhandler Rejects the Screen',
  },
  '@': {
    P: '2PT Attempt',
  },
  '#': {
    P: '3PT Attempt',
  },
  M: {
    S: 'Made Shot',
  },
  X: {
    S: 'Missed Shot',
  },
  V: {
    '#': '3 Second Violation',
    '%': '5 Second Violation',
    ')': '10 Second Violation',
    S: 'Shot Clock Violation',
    T: 'Travel Violation',
    O: 'Offensive Goaltending',
    L: 'Free Throw Lane Violation',
  },
};

/** Set of valid first keys for quick lookup. */
export const COMBO_FIRST_KEYS = new Set(Object.keys(HOTKEY_COMBOS));
