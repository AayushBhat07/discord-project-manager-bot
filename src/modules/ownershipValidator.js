/**
 * Validates that a caller has permission to modify a user's config.
 * A user can only modify their own config — not someone else's.
 */

/**
 * Check if callerId matches targetId (ownership validation).
 * @param {string} callerId - The ID of the user making the request
 * @param {string} targetId - The ID of the user whose config is being modified
 * @returns {boolean} - true only if callerId === targetId
 */
function validateOwnership(callerId, targetId) {
  return callerId === targetId;
}

/**
 * Shorthand helper for ownership check.
 * @param {string} callerId - The ID of the user making the request
 * @param {string} targetId - The ID of the user whose config is being modified
 * @returns {boolean} - true only if callerId === targetId
 */
function isOwnConfig(callerId, targetId) {
  return validateOwnership(callerId, targetId);
}

module.exports = {
  validateOwnership,
  isOwnConfig
};
