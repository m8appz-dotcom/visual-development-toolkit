// Authored fixture, no external application's source or assets.
exports.calculateDamage = function calculateDamage(baseDamage, armor) {
  return baseDamage <= 0 ? 0 : Math.max(1, baseDamage - armor);
};
