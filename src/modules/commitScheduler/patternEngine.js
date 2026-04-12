const moment = require('moment');
const commitEngine = require('./commitEngine');
const timestampProcessor = require('./timestampProcessor');

class PatternEngine {
  constructor() {
    this.templates = {
      A: this.getTemplateA(),
      B: this.getTemplateB(),
      C: this.getTemplateC(),
      heart: this.getHeartTemplate(),
      star: this.getStarTemplate(),
      check: this.getCheckTemplate(),
      smiley: this.getSmileyTemplate()
    };
  }

  getTemplateA() {
    const grid = [];
    for (let y = 0; y < 7; y++) {
      grid[y] = [];
      for (let x = 0; x < 5; x++) {
        if (x === 0 || x === 4 || (y === 0 && x > 0 && x < 4) || (y === 3 && x > 0 && x < 4)) {
          grid[y][x] = 1;
        } else {
          grid[y][x] = 0;
        }
      }
    }
    return { name: 'A', grid, width: 5, height: 7 };
  }

  getTemplateB() {
    const grid = [];
    for (let y = 0; y < 7; y++) {
      grid[y] = [];
      for (let x = 0; x < 5; x++) {
        if (x === 0 || (y === 0 && x < 4) || (y === 3 && x < 4) || (y === 6 && x < 4) || (x === 4 && y > 0 && y < 3) || (x === 4 && y > 3 && y < 6)) {
          grid[y][x] = 1;
        } else {
          grid[y][x] = 0;
        }
      }
    }
    return { name: 'B', grid, width: 5, height: 7 };
  }

  getTemplateC() {
    const grid = [];
    for (let y = 0; y < 7; y++) {
      grid[y] = [];
      for (let x = 0; x < 5; x++) {
        if (y === 0 || y === 6 || x === 0 || (y > 0 && y < 6 && x === 4)) {
          grid[y][x] = 1;
        } else {
          grid[y][x] = 0;
        }
      }
    }
    return { name: 'C', grid, width: 5, height: 7 };
  }

  getHeartTemplate() {
    const grid = [];
    const heartPattern = [
      [0, 1, 1, 0, 1, 1, 0],
      [1, 1, 1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1, 1, 1],
      [1, 1, 1, 1, 1, 1, 1],
      [0, 1, 1, 1, 1, 1, 0],
      [0, 0, 1, 1, 1, 0, 0],
      [0, 0, 0, 1, 0, 0, 0]
    ];
    for (let y = 0; y < 7; y++) {
      grid[y] = heartPattern[y];
    }
    return { name: 'Heart', grid, width: 7, height: 7 };
  }

  getStarTemplate() {
    const grid = [];
    const starPattern = [
      [0, 0, 0, 1, 0, 0, 0],
      [0, 0, 1, 1, 1, 0, 0],
      [1, 1, 1, 1, 1, 1, 1],
      [0, 1, 1, 1, 1, 1, 0],
      [0, 0, 1, 1, 1, 0, 0],
      [0, 1, 1, 0, 1, 1, 0],
      [1, 1, 0, 0, 0, 1, 1]
    ];
    for (let y = 0; y < 7; y++) {
      grid[y] = starPattern[y];
    }
    return { name: 'Star', grid, width: 7, height: 7 };
  }

  getCheckTemplate() {
    const grid = [];
    const checkPattern = [
      [1, 0, 0, 0, 0, 0, 0],
      [1, 1, 0, 0, 0, 0, 0],
      [0, 1, 1, 0, 0, 0, 0],
      [0, 0, 1, 1, 0, 0, 0],
      [0, 0, 0, 1, 1, 0, 0],
      [0, 0, 0, 0, 1, 1, 0],
      [0, 0, 0, 0, 0, 1, 1]
    ];
    for (let y = 0; y < 7; y++) {
      grid[y] = checkPattern[y];
    }
    return { name: 'Check', grid, width: 7, height: 7 };
  }

  getSmileyTemplate() {
    const grid = [];
    const smileyPattern = [
      [0, 1, 1, 1, 1, 1, 0],
      [1, 1, 1, 1, 1, 1, 1],
      [1, 1, 0, 1, 0, 1, 1],
      [1, 1, 1, 1, 1, 1, 1],
      [1, 1, 1, 0, 1, 1, 1],
      [1, 1, 0, 0, 0, 1, 1],
      [0, 1, 1, 1, 1, 1, 0]
    ];
    for (let y = 0; y < 7; y++) {
      grid[y] = smileyPattern[y];
    }
    return { name: 'Smiley', grid, width: 7, height: 7 };
  }

  getTemplate(name) {
    const key = name.toLowerCase();
    return this.templates[key] || null;
  }

  listTemplates() {
    return Object.keys(this.templates).map(key => ({
      id: key,
      name: this.templates[key].name,
      width: this.templates[key].width,
      height: this.templates[key].height
    }));
  }

  generatePatternCoordinates(templateName, options = {}) {
    const template = this.getTemplate(templateName);
    if (!template) {
      return { success: false, error: `Template "${templateName}" not found` };
    }

    const startWeek = options.startWeek || 0;
    const startDay = options.startDay || 0;

    const coordinates = [];
    const now = moment();
    const startOfWeek = now.clone().subtract(52 - startWeek, 'weeks').startOf('week');

    for (let y = 0; y < template.height; y++) {
      for (let x = 0; x < template.width; x++) {
        if (template.grid[y][x] === 1) {
          const date = startOfWeek.clone().add(startDay + x, 'weeks').add(y, 'days');
          coordinates.push({
            week: startWeek + x,
            day: y,
            date: date.format('YYYY-MM-DD'),
            intensity: options.intensity || 1
          });
        }
      }
    }

    return {
      success: true,
      coordinates,
      template: template.name,
      count: coordinates.length
    };
  }

  previewPattern(templateName, options = {}) {
    const template = this.getTemplate(templateName);
    if (!template) {
      return { success: false, error: `Template "${templateName}" not found` };
    }

    let output = '';
    for (let y = 0; y < template.height; y++) {
      let row = '';
      for (let x = 0; x < template.width; x++) {
        row += template.grid[y][x] === 1 ? '██' : '░░';
      }
      output += row + '\n';
    }

    return {
      success: true,
      preview: output,
      template: template.name,
      dimensions: `${template.width}x${template.height}`,
      cellCount: template.grid.flat().filter(c => c === 1).length
    };
  }

  async executePattern(templateName, message, options = {}) {
    const coordsResult = this.generatePatternCoordinates(templateName, options);
    if (!coordsResult.success) {
      return coordsResult;
    }

    const dryRun = options.dryRun || false;
    const results = [];

    for (const coord of coordsResult.coordinates) {
      const commitMessage = options.customMessage 
        ? options.customMessage.replace('{date}', coord.date)
        : `${message} - ${coord.date}`;

      const result = await commitEngine.execute(commitMessage, coord.date, {
        push: options.push !== false,
        files: options.files || ['.'],
        dryRun
      });

      results.push({
        date: coord.date,
        week: coord.week,
        day: coord.day,
        success: result.success,
        error: result.error
      });

      if (options.delayBetweenCommits) {
        await new Promise(resolve => setTimeout(resolve, options.delayBetweenCommits));
      }
    }

    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;

    return {
      success: failCount === 0,
      total: results.length,
      succeeded: successCount,
      failed: failCount,
      results,
      dryRun
    };
  }

  createCustomPattern(grid, name = 'Custom') {
    if (!grid || !Array.isArray(grid)) {
      return { success: false, error: 'Invalid grid array' };
    }

    const height = grid.length;
    const width = grid[0]?.length || 0;

    if (width === 0 || height === 0) {
      return { success: false, error: 'Grid dimensions must be greater than 0' };
    }

    const validatedGrid = [];
    for (let y = 0; y < height; y++) {
      validatedGrid[y] = [];
      for (let x = 0; x < width; x++) {
        validatedGrid[y][x] = grid[y][x] > 0 ? 1 : 0;
      }
    }

    const template = {
      name,
      grid: validatedGrid,
      width,
      height
    };

    const customKey = name.toLowerCase().replace(/\s+/g, '_');
    this.templates[customKey] = template;

    return {
      success: true,
      template: {
        id: customKey,
        name,
        width,
        height,
        cellCount: validatedGrid.flat().filter(c => c === 1).length
      }
    };
  }
}

module.exports = new PatternEngine();