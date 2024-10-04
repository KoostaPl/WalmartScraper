import json


class JsonExportPipeline:
    def open_spider(self, spider):
        self.items = {}

    def close_spider(self, spider):
        for keyword, items in self.items.items():
            items_sorted = sorted(
                items,
                key=lambda x: (
                    -(
                        x.get("averageRating") or 0
                    ),  # Sorting by rating 
                    x.get("price") or float("inf"),  # Sorting by price
                ),
            )

            # Saving sorted items to a single file
            self.save_to_file(f"{keyword}_sorted.json", items_sorted)

    def save_to_file(self, filename, items):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=4)

    def process_item(self, item, spider):
        keyword = item.get("findingObject", "unknown").replace(" ", "_")

        if keyword not in self.items:
            self.items[keyword] = []

        self.items[keyword].append(dict(item))
        return item
