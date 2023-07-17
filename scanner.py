import wx
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import threading
import time

lock = threading.Lock()

pluginName = []
pluginSlug = ['Elementor', 'Jetpack','woocommerce-services','unlimited-elements-for-elementor','custom-twitter-feeds','contact-form-entries',
'wp-piwik','add more plugin name here']

source = {}


def analyzeWebsite(url, result, resultMeta, resultScript):
    with lock:
        #limit to 1200 links
        if len(result) > 1200:
            return

        parsed_url = urlparse(url)
        initial_domain = urlparse(result[0]).netloc
        if parsed_url.netloc != initial_domain:
            result.append(url)
            return

    response = requests.get(url)
    html_content = response.text
    base_url = response.url

    soup = BeautifulSoup(html_content, 'html.parser')
        
    a_tags = soup.find_all('a')
    meta_tags = soup.find_all('meta')
    script_tags = soup.find_all('script')
    
    #seach for scripts
    for script in script_tags:
        src = script.get('src')
        type = script.get('type')
        embeddedScript = script.string
        if embeddedScript!=None:
            for plugin in pluginSlug:
                if plugin in embeddedScript:
                    with lock:
                        source[plugin] = src    
        
        if type:
            with lock:
                pass

        if src and src not in resultScript:
            absolute_src = urljoin(base_url, src)
            parsed_url = urlparse(absolute_src)
            if parsed_url.scheme not in ['http', 'https']:
                resultScript.append(url)
                return 
            else:
                with lock:
                    resultScript.append(src)
                analyzeWebsite(absolute_src, result, resultMeta,resultScript)

    #seacrh for meta tags
    for meta in meta_tags:
        name = meta.get('name')
        content = meta.get('content')
        property = meta.get('property')
        if meta and meta not in resultMeta:
            for plugin in pluginSlug:
                if plugin in meta:
                    with lock:
                        source[plugin] = meta
            with lock:
                resultMeta.append(meta)

    #search for links   
    for a in a_tags:
        href = urljoin(base_url, a.get('href'))
        if href and href != '#' and href not in result:
            with lock:
                result.append(href)
            print("Link:", href)
            analyzeWebsite(href, result, resultMeta, resultScript)

    return 

class UI(wx.App):
    def OnInit(self):
        self.frame = wx.Frame(None, title="My App")
        panel = wx.Panel(self.frame)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl = wx.TextCtrl(panel)
        sizer.Add(self.text_ctrl, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(sizer)

        self.button = wx.Button(panel, label="Analyze")
        sizer.Add(self.button, 0, wx.ALL, 10)
        self.button.Bind(wx.EVT_BUTTON, self.onSearchClick)

        self.frame.Show()
        return True

    def onSearchClick(self, event):
        website_url = self.text_ctrl.GetValue()
        threadNum = 4
        resultLink = [website_url]
        resultScript = []
        resultMeta = []
        link_threads = []

        
        start_time = time.time()

        # Start link analysis threads
        for i in range(threadNum):
            thread = threading.Thread(target=analyzeWebsite, args=(website_url, resultLink, resultMeta, resultScript))
            link_threads.append(thread)
            thread.start()

        # Wait for link analysis threads to finish
        for thread in link_threads:
            thread.join()
        
        end_time = time.time()
        print(resultMeta)
        print(resultScript)


                
        print ('Plugin:',list(source.keys()))
        
        print(end_time - start_time)


if __name__ == "__main__":
    app = UI()
    app.MainLoop()
