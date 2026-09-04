export const TEAMS = {
  1:  { code: 'NOR', color: '#F47600' },
  3:  { code: 'VER', color: '#4781D7' },
  5:  { code: 'BOR', color: '#F50537' },
  6:  { code: 'HAD', color: '#4781D7' },
  10: { code: 'GAS', color: '#00A1E8' },
  11: { code: 'PER', color: '#909090' },
  12: { code: 'ANT', color: '#00D7B6' },
  14: { code: 'ALO', color: '#229971' },
  16: { code: 'LEC', color: '#ED1131' },
  18: { code: 'STR', color: '#229971' },
  23: { code: 'ALB', color: '#1868DB' },
  27: { code: 'HUL', color: '#F50537' },
  30: { code: 'LAW', color: '#6C98FF' },
  31: { code: 'OCO', color: '#9C9FA2' },
  41: { code: 'LIN', color: '#6C98FF' },
  43: { code: 'COL', color: '#00A1E8' },
  44: { code: 'HAM', color: '#ED1131' },
  55: { code: 'SAI', color: '#1868DB' },
  63: { code: 'RUS', color: '#00D7B6' },
  77: { code: 'BOT', color: '#909090' },
  81: { code: 'PIA', color: '#F47600' },
  87: { code: 'BEA', color: '#9C9FA2' },
}

// Fallback for any driver with no mapping
export const teamOf = (num) => TEAMS[num] ?? { code: String(num), color: '#9aa0a6' }
