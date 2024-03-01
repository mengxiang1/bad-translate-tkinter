from tkinter import *
from tkinter import filedialog
from tkinter import ttk

from utils import *
import configparser


import googletrans
import re
import random
import asyncio
import traceback
import sys
import os


class App:
    async def exec(self):
        self.window = Window(asyncio.get_event_loop())
        await self.window.show()
        
        
class Window:
    def __init__(self, loop):
        #load configs from file
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.windowConfig = self.config["window"]
        self.optionsConfig = self.config["options"]

        #create stuff
        self.loop = loop
        self.root=Tk()
        self.width, self.height = int(self.windowConfig["width"]), int(self.windowConfig["height"])
        if self.height < 320 or self.width < 480:
            self.height = 320
            self.width = 480
        self.root.wm_geometry(f"{self.width}x{self.height}")
        self.root.wm_state(self.windowConfig["state"])
        self.root.wm_title("Bad Translator")
        self.root.wm_iconbitmap("icon.ico")
        self.translator = googletrans.Translator()
        self.file = ""

        self.options = [
            "all",
            "per word",
            "per sentence",
            "per newline"
        ]
        self.currentlyTranslating = 0
        self.status = StringVar()

        if self.root.state() == "zoomed":
            print(self.root.winfo_screenheight())
            self.text = Text(self.root, font="consolas 10", wrap=WORD, width=300, height=self.root.winfo_screenheight()/17 - 10)
        else:
            self.text = Text(self.root, font="consolas 10", wrap=WORD, width=300, height=self.height/17 - 10)
        self.level = Scale(self.root, from_=5, to=100, orient=HORIZONTAL, length=300)
        self.mode = StringVar(self.root)
        self.mode.set("all")
        self.modeMenu = OptionMenu(self.root, self.mode, *self.options)
        self.translateButton = ttk.Button(self.root, text="Bad Translate", command=lambda: self.loop.create_task(self.run()))
        self.output = ttk.Label(self.root, textvariable=self.status, relief=RIDGE, width=40)

        self.load = ttk.Button(self.root, text="Load", command=self.loadFile)
        self.save = ttk.Button(self.root, text="Save", command=self.saveFile)

        #placing stuff
        self.text.grid(row=0, column=0, columnspan=2)

        Label(self.root, text="Distortion Level").grid(row=1, column=0, sticky=E)
        self.level.grid(row=1, column=1, sticky=W)       

        Label(self.root, text="Mode").grid(sticky=E)
        self.modeMenu.grid(row=2, column=1, sticky=W)

        Label(self.root, text="Debug Output").grid(sticky=E)
        self.output.grid(row=3, column=1, sticky=W)

        self.load.grid(row=4, column=0, sticky=E)
        self.save.grid(row=4, column=1, sticky=W)
        self.translateButton.grid(row=5, columnspan=2)


        self.root.grid_columnconfigure((0,1), weight=1, uniform="column")
        for row_num in range(self.root.grid_size()[1]):
            self.root.grid_rowconfigure(row_num, pad=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind('<Control-r>', self.reload)
        self.root.bind('<Control-s>', self.saveFile)
        self.closing = False

    def close(self):
        self.on_closing()
        self.closing = True

    def on_closing(self):
        if self.root.state() != "zoomed":
            self.config.set("window", "width", str(self.root.winfo_width()))
            self.config.set("window", "height", str(self.root.winfo_height()))
        self.config.set("window", "state", self.root.state())
        self.config.write(open("config.ini", "w"))
        self.root.destroy()
    
    def reload(self, e):
        self.on_closing()
        python = sys.executable
        os.execl(python, python, * sys.argv)
        

    def loadFile(self):
            self.file = filedialog.askopenfilename()
            print(self.file)
            try:
                f = open(self.file, "r", encoding="utf-8")
            except FileNotFoundError:
                self.status.set("Failed to load file")
            else:
                self.root.wm_title(f"Bad Translator - {self.file}")
                self.text.replace(1.0, END, f.read())
                f.close()
                self.status.set("File loaded")
           
    def saveFile(self, *e):
        if self.file == "":
            self.file = filedialog.asksaveasfilename(filetypes=[("sussy files", "*.txt")])
        try:
            f = open(self.file, "w", encoding="utf-8")
        except:
            self.status.set("Failed to save and load file")
        else:
            f.write(self.text.get(1.0, END))
            f.close()
            self.status.set("File saved")
            self.root.wm_title(f"Bad Translator - {self.file}")
                
    async def show(self):
        while not self.closing:
            self.root.update()
            await asyncio.sleep(.1)
    
    async def run(self):
        self.status.set("Translating")
        try:
            text = self.text.get(SEL_FIRST, SEL_LAST)
        except Exception as e:
            self.status.set("Please make a selection")
        else:
            self.currentlyTranslating += 1
            mode = self.options.index(self.mode.get())
            times = int(self.level.get())

            self.text.tag_add(str(self.currentlyTranslating), SEL_FIRST, SEL_LAST)
            self.text.tag_configure(str(self.currentlyTranslating), background='yellow', relief='raised')
            

            def translate(text):
                for _ in range(times):
                    newlang = random.choice(list(googletrans.LANGUAGES))
                    text = self.translator.translate(text=text, dest=newlang).text
                return self.translator.translate(text=text, dest='en').text

            try:
                match mode:
                    case 0:
                            final = await run_blocking_io(translate, text)
                            self.text.replace(self.text.tag_ranges(str(self.currentlyTranslating))[0], self.text.tag_ranges(str(self.currentlyTranslating))[1], final)
                            self.status.set("Translation complete")
                    case 1:
                        parsed = re.split("(\W+)", text)
                        print(parsed)
                        for i in range(len(parsed)):
                            if parsed[i] == "" or i % 2 == 1:
                                continue
                            self.status.set("Translating: " + parsed[i])
                            print(parsed[i])
                            parsed[i] = await run_blocking_io(translate, parsed[i])
                        self.text.replace(self.text.tag_ranges(str(self.currentlyTranslating))[0], self.text.tag_ranges(str(self.currentlyTranslating))[1], "".join(parsed))
                    case 2:
                        text = text.rstrip('\n')
                        parsed = re.split("((?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s)+", text)
                        print(parsed)
                        for i in range(len(parsed)):
                            if parsed[i] == "" or i % 2 == 1:
                                continue
                            self.status.set("Translating: " + parsed[i])
                            print(parsed[i])
                            parsed[i] = await run_blocking_io(translate, parsed[i])
                        self.text.replace(self.text.tag_ranges(str(self.currentlyTranslating))[0], self.text.tag_ranges(str(self.currentlyTranslating))[1], "".join(parsed))

            except Exception as e:
                self.status.set(str(e))
                print(e)
                traceback.print_exc()
            else:
                self.status.set("Translation Complete")
            self.text.tag_delete(str(self.currentlyTranslating))
            self.currentlyTranslating -= 1
    


asyncio.run(App().exec())