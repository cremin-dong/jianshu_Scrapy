# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import codecs
import json

#将数据存储到Json文件
class JsonFilePipeline(object):

    def __init__(self):
        self.file = codecs.open('jianshu.json', 'wb', encoding='utf-8')

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(line)
        return item

    def spider_closed(self, spider):
        self.file.close()


#将数据存储到mysql数据库
from twisted.enterprise import adbapi


class MySQLStorePipeline(object):
    #采用异步的方式插入数据

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            port=settings["MYSQL_PORT"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWD"],
            db=settings["MYSQL_DB"],
            use_unicode=True,
            charset="utf8mb4",
        )
        dbpool = adbapi.ConnectionPool("pymysql", **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        """
        使用twisted将mysql插入变成异步
        :param item:
        :param spider:
        :return:
        """
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error)


    def handle_error(self, failure):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):

        # 具体插入数据
        insert_sql = 'insert into article(title,author,publish_time,content,cover_image_url,source_web,source_url) ' \
                     'VALUES (%s,%s,%s,%s,%s,%s,%s)'
        cursor.execute(insert_sql, (item["title"],item["author"],item["publish_time"],item["content"],
                                    item["cover_image_url"],item["source_web"],item["source_url"]))


#图像保存管道
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http import Request

class MyImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            if image_url.startswith('http:') == False:
                image_url = '%s%s' % ('http:', image_url)
            yield Request(image_url)

