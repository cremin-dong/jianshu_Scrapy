# -*- coding: utf-8 -*-
import scrapy
import hashlib

from scrapy_splash import SplashRequest
from jianshu.items import JianshuItem
from scrapy.utils.python import to_bytes
from bs4 import BeautifulSoup


class JianshuspiderSpider(scrapy.Spider):

    name = 'jianshuspider'
    allowed_domains = ['jianshu.com']
    start_urls = [
        'https://www.jianshu.com'
    ]
    total = 0

    def start_requests(self):

        script = """
        function main(splash, args)
          splash:go(args.url)
          
          -- 滚动到底部
          local scrollToEnd = splash:jsfunc([[
          function () {
                 var h = document.documentElement.scrollHeight || document.body.scrollHeight;
                 window.scrollTo(0,h);            
          }
          ]])
          
          -- 判断阅读更多是否显示
          local loadMoreNoDisplay = splash:jsfunc([[
          function () {
                 
                 return document.getElementsByClassName('load-more').length == 0 ? true : false;       
          }
          ]])
    
          
          -- 循化下拉，直到“阅读更多”按钮出现
          while( splash:select('a.load-more') == nil)
            do
               scrollToEnd()
               splash:wait(1)
            end

          -- 触发点击“阅读更多”事件
          splash:select('a.load-more'):click()
          splash:wait(1)
          
          return {
             html = splash:html(),
          } 
        end
        """

        for url in self.start_urls:
            yield SplashRequest(url, self.parse,
                                endpoint='execute',
                                cache_args=['lua_source'],
                                args={'wait': 3, 'lua_source': script},
                                )

    def parse(self, response):
        for li in response.css('li[data-note-id]'):
            detail_url = li.css('div.content > a.title::attr("href")').extract_first()
            yield response.follow(detail_url, self.parse_detail)

    def parse_detail(self, response):

        for li in response.css('div.post > div.article'):

            item = JianshuItem()
            item["title"] = li.css("h1.title::text").extract_first()
            item["author"] = li.css("div.author > div.info > span.name > a::text").extract_first()
            item["publish_time"] = li.css("div.author > div.info > div.meta > span.publish-time::text").extract_first()

            content_node = li.xpath('./div[@class="show-content"]')
            content_text = content_node.extract_first()

            image_urls = content_node.css("img::attr(data-original-src)")
            item["image_urls"] = image_urls.extract()

            soup = BeautifulSoup(content_text)
            for img in soup.findAll('img'):
                url =  'http:' + img['data-original-src']
                image_guid = hashlib.sha1(to_bytes(url)).hexdigest()  # change to request.url after deprecation
                img['src'] = image_guid + '.jpg'
                img['data-original-src'] = ""
                content_text = str(soup)

            item["content"] = content_text

            if image_urls.extract_first() is not None:
                url = 'http:' +image_urls.extract_first()
                image_guid = hashlib.sha1(to_bytes(url)).hexdigest()  # change to request.url after deprecation
                item["cover_image_url"] = image_guid + '.jpg'
            else:
                item["cover_image_url"] = None

            item["source_web"] = "jianshu"
            item["source_url"] = response.url
            yield item
