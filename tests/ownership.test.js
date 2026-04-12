const { validateOwnership, isOwnConfig } = require('../src/modules/ownershipValidator');

describe('ownershipValidator', () => {
  describe('validateOwnership', () => {
    it('returns true when callerId equals targetId', () => {
      expect(validateOwnership('123', '123')).toBe(true);
    });

    it('returns false when callerId differs from targetId', () => {
      expect(validateOwnership('123', '456')).toBe(false);
    });

    it('returns false for different string representations', () => {
      expect(validateOwnership('123', '0123')).toBe(false);
    });
  });

  describe('isOwnConfig', () => {
    it('returns true when caller owns the config', () => {
      expect(isOwnConfig('999', '999')).toBe(true);
    });

    it('returns false when caller does not own the config', () => {
      expect(isOwnConfig('999', '888')).toBe(false);
    });
  });
});
