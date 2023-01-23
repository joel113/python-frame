# -*- coding: utf-8 -*-
import epd7in5
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import pytz
from datetime import datetime, timedelta
from dateutil.tz import *
from time import sleep
import feedparser
import subprocess
import sys
import urllib, json
#import imagedata

EPD_WIDTH = 640
EPD_HEIGHT = 384

def main():
    epd = epd7in5.EPD()
    epd.init()
    page = ['news','mvg']
    tempText = 'Initial temperature text.'
    x = 0
    while True:
        image = Image.new('1', (EPD_WIDTH, EPD_HEIGHT), 1)    # 1: clear the frame
        draw = ImageDraw.Draw(image)

        # draw header
        drawHeader(draw)

        if(page[x] == 'news'):
        
            # draw news section
            topNews = retrieveNews('http://www.spiegel.de/schlagzeilen/eilmeldungen/index.rss')
            news = retrieveNews('http://www.spiegel.de/schlagzeilen/tops/index.rss')
            drawNewsSection(draw, topNews, news)

        else:
        
            # draw mvg section
            data = retrieveMvgData()
            drawMvgSection(draw, 'MVG Abfahrtszeiten', data)

        x = (x + 1) % 2
        
        # draw weather section
        tempText = retrieveWeather('http://api.openweathermap.org/data/2.5/weather?q=munich,de&appid=&lang=de&units=metric')

        # Only update the text if no error occured
        if tempText != -1:
            text = tempText
        
        drawWeatherSection(draw, text)

        # draw frame
        epd.display(epd.getbuffer(image))
	    
        sleep(240)

def drawHeader(draw):
    font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 24)
    date = datetime.now().strftime('%H:%M:%S %d.%m.%Y')
    text = 'Joel-Frame  Munchen, BY  ' + date
    draw.rectangle((0, 0, 640, 40), fill = 0)
    draw.text((10, 10), text, font = font, fill = 255)

### News Section ###

def drawMvgSection(draw, header, data):
    fontHeader = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 24)
    fontEntries = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 15)
    draw.rectangle((0, 40, 640, 80), fill = 0)
    draw.text((10,50), header, font = fontHeader, fill = 255)
    draw.text((20,90), data, font = fontEntries, fill = 0)

def retrieveMvgData():
    mvg = subprocess.check_output(['mvg','Südtiroler Straße']).decode('UTF-8')
    return mvg;

### News Section ###

def drawNewsSection(draw, topNews, news):
    # Draw the Spiegel Online Eilmeldungen
    filteredTopNews = filterNews(topNews, datetime.today()-timedelta(1))
    numberOfFilteredTopNews = len(filteredTopNews)
    if numberOfFilteredTopNews > 0:
        drawNews(draw, 'Spiegel Online Eilmeldungen', filteredTopNews)
        startDrawingNewsAt = 100 + numberOfFilteredTopNews * 20
        maximumNumberOfEntries = 9 - numberOfFilteredTopNews
    else:
        startDrawingNewsAt = 40
        maximumNumberOfEntries = 12
        
    # Draw the Spiegel Online Top Schlagzeilen
    filteredNews = filterNews(news, datetime.today()-timedelta(7))
    drawNews(draw, 'Spiegel Online Top Schlagzeilen', filteredNews, maximumNumberOfEntries=maximumNumberOfEntries, startDrawingAt=startDrawingNewsAt)

def retrieveNews(url):
    feed = feedparser.parse(url)
    news = []
    for entry in feed.entries:
        news.append(entry.published)
        news.append(entry.title)
    return news

def filterNews(news, filterUntilDate):
    filteredNews = []
    while len(news) > 1:
        newsDate = news.pop(0)
        newsEntry = news.pop(0)
        newsDateWithoutZ = newsDate[:len(newsDate)-6]
        newsDateFormated = datetime.strptime(newsDateWithoutZ, '%a, %d %b %Y %H:%M:%S')
        if(newsDateFormated >= filterUntilDate):
            filteredNews.append(newsEntry)
    return filteredNews

def drawNews(draw, header, news, maximumNumberOfEntries = 12, startDrawingAt=40):
    fontHeader = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 24)
    fontEntries = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 16)
    draw.rectangle((0, startDrawingAt, 640, startDrawingAt + 40), fill = 0)
    draw.text((10,startDrawingAt+10), header, font = fontHeader, fill = 255)
    x = startDrawingAt + 55
    i = 0
    for entry in news:
        draw.text((10,x), entry, font = fontEntries, fill = 0)
        x = x + 20
        i = i + 1
        if i >= maximumNumberOfEntries:
            break

### Weather Section ###

def retrieveWeather(url):
    try:
        data = json.loads(urllib.request.urlopen(url).read())
        temp = str(data['main']['temp'])
        weather = data['weather'][0]['description']
        sunrise = datetime.fromtimestamp(data['sys']['sunrise'],tz=pytz.utc).astimezone(tzlocal()).strftime('%H:%M')
        sunset = datetime.fromtimestamp(data['sys']['sunset'],tz=pytz.utc).astimezone(tzlocal()).strftime('%H:%M')
        text = temp + ' C' + chr(176) + ' und ' + weather + ', Sonne von ' + sunrise + ' bis ' + sunset
        return text
    except ValueError:
        print('JSON Weather Decoding failed')
        return -1

def drawWeatherSection(draw, text):
    # Draw the Weather into the footer
    draw.rectangle((0, 344, 640, 384), fill = 0)
    drawWeather(draw, text);
                            
def drawWeather(draw, text):
    font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 20)
    draw.text((10, 354), text, font = font, fill = 255)

if __name__ == '__main__':
    main()
