const { LRUCache } = require('lru-cache');

class MemoryCache {
  constructor() {
    this.store = new LRUCache({ max: 5000, ttl: 1000 * 60 * 10 });
  }
  async get(key) {
    return this.store.get(key) ?? null;
  }
  async set(key, value) {
    this.store.set(key, value);
  }
  async del(key) {
    this.store.delete(key);
  }
}

const cache = new MemoryCache();

console.log('Cache backend: in-memory LRU');

module.exports = cache;