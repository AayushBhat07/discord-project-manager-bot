const moment = require('moment');
const timestampProcessor = require('../../src/modules/commitScheduler/timestampProcessor');

describe('TimestampProcessor', () => {
  describe('parse', () => {
    test('should parse YYYY-MM-DD format', () => {
      const result = timestampProcessor.parse('2024-01-15');
      expect(result.isValid()).toBe(true);
      expect(result.format('YYYY-MM-DD')).toBe('2024-01-15');
    });

    test('should parse YYYY-MM-DD HH:mm format', () => {
      const result = timestampProcessor.parse('2024-01-15 14:30');
      expect(result.isValid()).toBe(true);
      expect(result.format('YYYY-MM-DD HH:mm')).toBe('2024-01-15 14:30');
    });

    test('should parse relative date "yesterday"', () => {
      const result = timestampProcessor.parse('yesterday');
      expect(result.isValid()).toBe(true);
      expect(result.isSame(moment().subtract(1, 'day'), 'day')).toBe(true);
    });

    test('should parse relative date "3 days ago"', () => {
      const result = timestampProcessor.parse('3 days ago');
      expect(result.isValid()).toBe(true);
      expect(result.isSame(moment().subtract(3, 'days'), 'day')).toBe(true);
    });

    test('should parse relative date "in 2 weeks"', () => {
      const result = timestampProcessor.parse('in 2 weeks');
      expect(result.isValid()).toBe(true);
      expect(result.isSame(moment().add(2, 'weeks'), 'day')).toBe(true);
    });

    test('should throw on invalid input', () => {
      expect(() => timestampProcessor.parse('')).toThrow();
      expect(() => timestampProcessor.parse(null)).toThrow();
    });
  });

  describe('validate', () => {
    test('should validate a valid timestamp', () => {
      const result = timestampProcessor.validate('2024-01-15');
      expect(result.valid).toBe(true);
      expect(result.parsed.isValid()).toBe(true);
    });

    test('should reject timestamps more than 24 hours in future', () => {
      const result = timestampProcessor.validate('2030-01-01');
      expect(result.valid).toBe(false);
    });

    test('should reject timestamps before Git epoch', () => {
      const result = timestampProcessor.validate('1969-01-01');
      expect(result.valid).toBe(false);
    });
  });

  describe('toISOString', () => {
    test('should convert moment object to ISO string', () => {
      const m = moment('2024-01-15 14:30:00');
      const result = timestampProcessor.toISOString(m);
      expect(result).toContain('2024-01-15');
    });
  });

  describe('toGitDate', () => {
    test('should convert to git date format', () => {
      const m = moment('2024-01-15 14:30:00');
      const result = timestampProcessor.toGitDate(m);
      expect(result).toContain('2024-01-15');
    });
  });

  describe('getWeekOffset', () => {
    test('should return start of week for given week number', () => {
      const result = timestampProcessor.getWeekOffset(52);
      expect(result.isValid()).toBe(true);
    });
  });

  describe('getDateForCell', () => {
    test('should return correct date for week and day', () => {
      const weekStart = moment().startOf('week');
      const result = timestampProcessor.getDateForCell(weekStart, 0);
      expect(result.isValid()).toBe(true);
    });
  });
});