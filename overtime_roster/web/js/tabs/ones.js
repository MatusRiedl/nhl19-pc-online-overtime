// Ones (1v1v1, each for himself): pure helpers of the Multiplayer tab's Ones parts, no imports, so a test can run them
// in node (tests/test_ones.py).

const ORDINALS = ['1st', '2nd', '3rd', '4th'];

// Each player's place from the goals, after his name (the most goals win, ties share a place, as the server places
// them: history._resolve_ones); no places while a score is missing
export const onesPlaced = (sides) => (sides.every((x) => x.score != null)
  ? sides.map((x) => ({ ...x, names: [`${x.names.join(', ')} · ${ORDINALS[sides.filter((y) => y.score > x.score).length]}`] }))
  : sides);
