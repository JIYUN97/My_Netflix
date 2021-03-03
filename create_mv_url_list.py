from selenium import webdriver
from time import sleep

from bs4 import BeautifulSoup

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.my_netflix

#ChromeDriver로 접속, 자원 로딩시간 3초
driver = webdriver.Chrome('./chromedriver')

# 영화
url = "https://www.themoviedb.org/movie?language=ko-KR"

scroll_down = "window.scrollTo(0, document.body.scrollHeight);"

driver.get(url)  # 드라이버에 해당 url의 웹페이지를 띄웁니다.
sleep(1)  # 페이지가 로딩되는 동안 1초 간 기다립니다.

btn_filter = driver.find_element_by_xpath('//*[@id="media_v4"]/div/div/div[2]/div[1]/div[2]/div[1]')

# 필터 버튼 클릭
btn_filter.click()
sleep(1)

btn_calendar = driver.find_elements_by_css_selector('div.year_column span.k-select')

# from 캘린더 클릭
btn_calendar[0].click()
sleep(1)

btn_back = driver.find_elements_by_css_selector('div.k-calendar-header > a')

# from 연도 선택 화면으로 이동
btn_back[0].click()
btn_back[0].click()
sleep(1)

# from 날짜 선택
for i in [1, 0, 3]:
  pick = driver.find_elements_by_css_selector('td[role=gridcell]')

  pick[i].click()
  
sleep(1)

# # to 캘린더 클릭
# btn_calendar[1].click()
# sleep(1)

# btn_today = driver.find_elements_by_css_selector('div.k-calendar-header > span > a')

# btn_today[1].click()
# sleep(1)

# Scroll Down
driver.execute_script(scroll_down)

btn_where = driver.find_element_by_xpath('//*[@id="media_v4"]/div/div/div[2]/div[1]/div[3]/div[1]')

btn_where.click()
sleep(1)

btn_netflix = driver.find_element_by_xpath('//*[@id="ott_providers"]/li[1]/a')
btn_netflix.click()

btn_search = driver.find_element_by_xpath('//*[@id="media_v4"]/div/div/div[2]/div[1]/div[4]/p/a')
btn_search.click()
sleep(1)

# Scroll Down
driver.execute_script(scroll_down)

btn_more = driver.find_element_by_xpath('//*[@id="pagination_page_1"]/p/a')
btn_more.click()
sleep(1)

for i in range(30):
  # Scroll Down
  driver.execute_script(scroll_down)
  sleep(0.5)

req = driver.page_source  # html 정보를 가져옵니다.
driver.quit()  # 정보를 가져왔으므로 드라이버는 꺼줍니다.

soup = BeautifulSoup(req, 'html.parser')

for i in range(1,30):

  page = soup.select_one('#page_' + str(i))
  contents = page.select('div.card > div.content')

  for content in contents:
    url_path = content.select_one('h2 > a')['href']
    title = content.select_one('h2 > a').text

    doc = {
    "url_path": url_path,
    "title": title}
    
    db.movie_url.insert_one(doc)
