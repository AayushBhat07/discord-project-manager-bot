const patternEngine = require('../src/modules/commitScheduler/patternEngine');

describe('PatternEngine', () => {
  describe('getTemplate', () => {
    test('should return template by name', () => {
      const template = patternEngine.getTemplate('A');
      expect(template).not.toBeNull();
      expect(template.name).toBe('A');
    });

    test('should return template case-insensitively', () => {
      const template = patternEngine.getTemplate('heart');
      expect(template).not.toBeNull();
      expect(template.name).toBe('Heart');
    });

    test('should return null for non-existent template', () => {
      const template = patternEngine.getTemplate('non-existent');
      expect(template).toBeNull();
    });
  });

  describe('listTemplates', () => {
    test('should list all available templates', () => {
      const templates = patternEngine.listTemplates();
      expect(templates.length).toBeGreaterThan(0);
      expect(templates).toContainEqual(expect.objectContaining({ id: 'A', name: 'A' }));
      expect(templates).toContainEqual(expect.objectContaining({ id: 'heart', name: 'Heart' }));
    });
  });

  describe('generatePatternCoordinates', () => {
    test('should generate coordinates for a template', () => {
      const result = patternEngine.generatePatternCoordinates('A');
      expect(result.success).toBe(true);
      expect(result.coordinates).toBeInstanceOf(Array);
      expect(result.coordinates.length).toBeGreaterThan(0);
    });

    test('should fail for non-existent template', () => {
      const result = patternEngine.generatePatternCoordinates('non-existent');
      expect(result.success).toBe(false);
    });

    test('should apply startWeek option', () => {
      const result = patternEngine.generatePatternCoordinates('A', { startWeek: 10 });
      expect(result.success).toBe(true);
      expect(result.coordinates[0].week).toBe(10);
    });

    test('should apply startDay option', () => {
      const result = patternEngine.generatePatternCoordinates('A', { startDay: 3 });
      expect(result.success).toBe(true);
      expect(result.coordinates[0].day).toBe(3);
    });
  });

  describe('previewPattern', () => {
    test('should generate preview for a template', () => {
      const result = patternEngine.previewPattern('A');
      expect(result.success).toBe(true);
      expect(result.preview).toContain('██');
      expect(result.dimensions).toBeDefined();
    });

    test('should fail for non-existent template', () => {
      const result = patternEngine.previewPattern('non-existent');
      expect(result.success).toBe(false);
    });

    test('should count cells correctly', () => {
      const result = patternEngine.previewPattern('A');
      expect(result.cellCount).toBeGreaterThan(0);
    });
  });

  describe('executePattern', () => {
    test('should execute pattern in dry-run mode', async () => {
      const result = await patternEngine.executePattern('A', 'Test commit', {
        dryRun: true,
        push: false
      });
      expect(result).toHaveProperty('success');
      expect(result.dryRun).toBe(true);
    });
  });

  describe('createCustomPattern', () => {
    test('should create a custom pattern', () => {
      const grid = [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
      ];
      const result = patternEngine.createCustomPattern(grid, 'Box');
      expect(result.success).toBe(true);
      expect(result.template.name).toBe('Box');
      expect(result.template.width).toBe(3);
      expect(result.template.height).toBe(3);
    });

    test('should fail with invalid grid', () => {
      const result = patternEngine.createCustomPattern([], 'Empty');
      expect(result.success).toBe(false);
    });
  });
});