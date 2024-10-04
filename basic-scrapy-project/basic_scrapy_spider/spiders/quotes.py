import scrapy
import math
import json
import random
from urllib.parse import urlencode


class WalmartProduct(scrapy.Item):
    findingObject = scrapy.Field()
    url = scrapy.Field()
    page = scrapy.Field()
    position = scrapy.Field()
    id = scrapy.Field()
    type = scrapy.Field()
    name = scrapy.Field()
    brand = scrapy.Field()
    model = scrapy.Field()
    averageRating = scrapy.Field()
    shortDescription = scrapy.Field()
    thumbnailUrl = scrapy.Field()
    price = scrapy.Field()
    currencyUnit = scrapy.Field()


class WalmartScraper(scrapy.Spider):
    name = "walmart"

    def start_requests(self):
        user_input = input("Enter the desired keywords separated by commas: ")
        keyword_list = [keyword.strip() for keyword in user_input.split(",")]

        random.shuffle(keyword_list)

        for keyword in keyword_list:
            payload = {
                "q": keyword,
                "sort": "best_seller",
                "page": 1,
                "affinityOverride": "default",
            }
            url_of_product = "https://www.walmart.com/search?" + urlencode(payload)
            yield scrapy.Request(
                url=url_of_product,
                callback=self.parse_page,
                meta={"keyword": keyword, "page": 1},
            )

    def parse_page(self, response):
        page = response.meta["page"]
        keyword = response.meta["keyword"]
        script_tag = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()

        if script_tag is None:
            self.logger.error(
                f"No script tag found for keyword: {keyword}, page: {page}"
            )
            return

        json_blob = json.loads(script_tag)
        itemStacks = (
            json_blob.get("props", {})
            .get("pageProps", {})
            .get("initialData", {})
            .get("searchResult", {})
            .get("itemStacks", [])
        )
        if not itemStacks:
            self.logger.error(f"No items found for keyword: {keyword}, page: {page}")
            return

        list_of_products = itemStacks[0].get("items", [])
        for idx, product in enumerate(list_of_products):
            product_url = (
                "https://www.walmart.com"
                + product.get("canonicalUrl", "").split("?")[0]
            )
            yield scrapy.Request(
                url=product_url,
                callback=self.scrap_item_info,
                meta={"keyword": keyword, "page": page, "position": idx + 1},
            )

        total_count_of_products = itemStacks[0].get("count", 0)
        max_pages = (
            min(math.ceil(total_count_of_products / 40), 5)
            if total_count_of_products > 0
            else 1
        )

        for pg in range(2, max_pages + 1):
            payload = {
                "q": keyword,
                "sort": "best_seller",
                "page": pg,
                "affinityOverride": "default",
            }
            find_url = "https://www.walmart.com/search?" + urlencode(payload)
            yield scrapy.Request(
                url=find_url,
                callback=self.parse_page,
                meta={"keyword": keyword, "page": pg},
            )

    def scrap_item_info(self, response):
        script_tag = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if script_tag is not None:
            json_blob = json.loads(script_tag)
            raw_item_info = (
                json_blob.get("props", {})
                .get("pageProps", {})
                .get("initialData", {})
                .get("data", {})
                .get("product", {})
            )

            item = WalmartProduct()
            item["findingObject"] = response.meta["keyword"]
            item["url"] = "https://www.walmart.com" + raw_item_info.get("canonicalUrl")
            item["page"] = response.meta["page"]
            item["position"] = response.meta["position"]
            item["id"] = raw_item_info.get("id")
            item["type"] = raw_item_info.get("type")
            item["brand"] = raw_item_info.get("brand")
            item["name"] = raw_item_info.get("name")
            item["model"] = raw_item_info.get("model")
            item["averageRating"] = raw_item_info.get("averageRating")
            item["shortDescription"] = raw_item_info.get("shortDescription")
            item["thumbnailUrl"] = raw_item_info.get("imageInfo", {}).get(
                "thumbnailUrl"
            )
            item["price"] = (
                raw_item_info.get("priceInfo", {}).get("currentPrice", {}).get("price")
            )
            item["currencyUnit"] = (
                raw_item_info.get("priceInfo", {})
                .get("currentPrice", {})
                .get("currencyUnit")
            )

            yield item
