get_rate in rates/lookup.py hits upstream on every invoice render and it's getting slow. should we throw an in-process lru on it or stand up a redis cache? what would you do
