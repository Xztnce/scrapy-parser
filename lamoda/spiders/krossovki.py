import scrapy


class KrossovkiSpider(scrapy.Spider):
    name = 'krossovki'
    allowed_domains = ['lamoda.ru']
    start_urls = ['https://www.lamoda.ru/c/5318/shoes-vysokiekrossovkimuj/?page=1']

    pages = 8
    def start_requests(self):
        for page in range(1, 1 + self.pages):
            url = f'https://www.lamoda.ru/c/5318/shoes-vysokiekrossovkimuj/?page={page}'
            yield scrapy.Request(url, callback = self.parse_pages)

    def parse_pages(self, response):
        for href in response.css('a.products-list-item__link::attr(href)').extract():
            url = response.urljoin(href)
            yield scrapy.Request(url, callback = self.parse)

    def parse(self, response):

        #Получение иерархии разделов
        section = response.css('span.js-breadcrumbs__item-text::text').getall()
        section = [line.replace(' ', '') for line in section]
        section = [line.replace('\n', '') for line in section]
        section.pop(0)

        #Получение данных о наличии товара и оставшемся кол-ве
        stock = {}
        st = response.css('div.ii-product__buy::attr(data-available_sizes)').get()
        if int(st) > 0:
            stock['in_stock'] = True
        else:
            stock['in_stock'] = False

        stock['count'] = int(st)

        #Получение изображений товара
        set_images = response.css('img').xpath('@src').getall()
        assets = {'main_image': response.css('div.ii-product::attr(data-image)').get(),
                  'set_images' : set_images,
                  }

        #Получение цен и скидок товара
        info = response.xpath('//*[@id="vue-root"]/x-app-content/script/text()').getall()
        tmp = info[0].split(',')
        tmp = [line.replace('\n', '') for line in tmp]        #Очистка "мусора"
        tmp = [line.replace(' ', '') for line in tmp]

        price_data = {}
        for i in tmp:
            if 'current' in i:
                price_data['current'] = i.split(':')[1].replace("'", '').replace('"', '')
            elif 'original' in i:
                price_data['original'] = i.split(':')[1].replace("'", '').replace('"', '')
            elif 'discountPercent' in i:
                price_data['sale_tag'] = 'Скидка '+i.split(':')[1].replace("'", '').replace('"', '')+'%'


        #Получение стороннмх характеристик со страницы товара
        param = response.css('span.ii-product__attribute-label::text').extract()
        value = response.css('span.ii-product__attribute-value::text').extract()

        param = [line.replace('\n','') for line in param]
        param = [line.replace(' ', '') for line in param]
        value = [line.replace('\n','') for line in value]
        value = [line.replace(' ', '') for line in value]

        parametrs = {}
        for i in range(len(param)):
            parametrs[param[i]] = value[i]

        metadata = {'description' : response.css('pre::text').extract(),
                    #str(response.css('span.ii-product__attribute-label::text').extract()) : response.css('span.ii-product__attribute-value::text').extract(),
                    'other_stats' : parametrs,
                    }
        #Словарь для json
        item = {
            'url' : response.request.url,
            'title' : response.css('div.ii-product::attr(data-name)').get(),
            'brand': response.css('div.ii-product::attr(data-brand)').get(),
            'section' : section,
            'price_data' : price_data,
            'stock' : stock,
            'assets': assets,
            'metadata': metadata,
            #'title': response.css('div.catalog-element-info js-catalog-item js-catalog-item-detail::attr(data-name)').extract(),
            #'brand': response.css('div.catalog-element-info js-catalog-item js-catalog-item-detail::attr(data-brand)').extract(),
        }

        yield item

