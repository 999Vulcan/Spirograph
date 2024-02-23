# -*- coding: iso-8859-15 -*-

from __future__ import division
from __future__ import print_function

version = "1.3"
host, port = "localhost", 54321

import sys
print("iSpirograph v. {0} by 999Vulcan\n".format(version))

if sys.version_info < (2, 7):
    print("Need Python 2.7 or greater")
    print("Exiting...")
    sys.exit()

try:
    from tkinter import *
    from _thread import *
    from queue import *
    from socketserver import *
    C = "©"
except:
    from Tkinter import *
    from thread import *
    from Queue import *
    from SocketServer import *
    C = "(c)"

from math import *
from random import *
from fractions import gcd
from socket import *
from threading import *
import time

Tick = 30
UpdateInterval = 30000

margin = 20

maxR = 300
maxN = 300

defC = "green"
defBG = "black"
defN = 100

minPrec = 100

StopThreads = False
SpiroCoords = Queue()
RunningThreads = Queue()
PercentDone = 0
OldPercentDone = 0

accuracies = (0.01, 0.05, 0.1, 0.3, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 50, 100, 200)
colors = ("black", "darkgrey", "grey", "lightgrey", "white", "lightgreen", "green", "yellow", "gold", "bisque",
          "orange", "brown", "maroon", "red", "magenta", "purple", "navy", "blue", "lightblue", "turquoise", "cyan")

class App:
    def __init__(self, parent):
        global maxX, maxY
        
        self.f = Frame(parent)
        self.f.grid()

        self.Random = Button(self.f, text="  Random  ", command=self.Randomize)
        self.Random.bind_all("<space>", self.Randomize)
        self.Random.grid(padx=5, pady=5, row=0, column=1)
        
        Label(self.f, text='R:').grid(padx=3, row=0, column=2)
        self.R = Spinbox(self.f, width=4, from_=-maxR*2, to=maxR*2, command=self.DrawSpiro)
        self.R.grid(row=0, column=3)
        
        Label(self.f, text='r:').grid(padx=3, row=0, column=4)
        self.r = Spinbox(self.f, width=4, from_=-maxR*2, to=maxR*2, command=self.DrawSpiro)
        self.r.grid(row=0, column=5)
        
        Label(self.f, text='O:').grid(padx=3, row=0, column=6)
        self.O = Spinbox(self.f, width=4, from_=-maxR*2, to=maxR*2, command=self.DrawSpiro)
        self.O.grid(row=0, column=7)
        
        Label(self.f, text='n:').grid(padx=5, row=0, column=8)
        self.n = Spinbox(self.f, width=3, from_=1, to=maxN*2, command=self.DrawSpiro)
        self.n.grid(row=0, column=9)

        self.Draw = Button(self.f, text="    Draw    ", command=self.DrawSpiro, default="active")
        self.Draw.bind_all("<Return>", self.DrawSpiro)
        self.Draw.grid(padx=10, row=0, column=10)

        self.acc = StringVar(self.f)
        self.acc.trace("w", self.DrawSpiro)
        Label(self.f, text='Sampling:').grid(padx=5, row=0, column=11)
        self.accmenu = OptionMenu(self.f, self.acc, *accuracies)
        self.accmenu["width"]=2
        self.accmenu.grid(padx=5, row=0, column=12)
        
        self.color = StringVar(self.f)
        self.color.set(defC)
        self.color.trace("w", self.DrawSpiro)
        Label(self.f, text='Color:').grid(padx=5, row=0, column=13)
        self.colormenu = OptionMenu(self.f, self.color, *colors)
        self.colormenu["width"]=7
        self.colormenu.grid(padx=5, row=0, column=14)
        
        self.bg = StringVar(self.f)
        self.bg.set(defBG)
        self.bg.trace("w", self.DrawSpiro)
        Label(self.f, text='BG:').grid(padx=5, row=0, column=15)
        self.bgmenu = OptionMenu(self.f, self.bg, *colors)
        self.bgmenu["width"]=7
        self.bgmenu.grid(padx=5, row=0, column=16)

        self.frz = Button(self.f, text=" Freeze ", command=self.Freeze)
        self.frz.grid(padx=4, row=0, column=17)

        self.clr = Button(self.f, text=" Clear ", command=self.Clear)
        self.clr.grid(padx=4, row=0, column=18)
        self.clr.bind_all("<Escape>", self.Clear)
        
        self.host = Entry(self.f)
        self.host.insert(0, host)
        self.host.grid(padx=10, row=0, column=19)

        self.canvas = Canvas(height=maxY)
        self.canvas.grid(row=1, sticky="SNEW")
        
        self.statusbar = Canvas(height=11)
        self.statusbar.grid(row=2, sticky="SNEW")

        self.line = 0
        self.status = 0
        self.percent = 0
        self.threadcount = 0
        self.queuesize = 0

        parent.update()
        maxX = self.canvas.winfo_width()
        maxY = self.canvas.winfo_height()

        self.IdleTask()
        self.Randomize()

    def Freeze(self):
        self.line = 0

    def Clear(self, *args):
        global PercentDone, OldPercentDone
        AbortThreads()
        self.canvas.delete(ALL)
        self.statusbar.delete(ALL)
        self.PrintC(self.bg.get())
        PercentDone, OldPercentDone = 0, 0

    def Randomize(self, *args):
        R = randint(-maxR, maxR)
        r = randint(-maxR, maxR)
        if r == 0: r = 1
        self.R.delete(0, END)
        self.R.insert(0, str(R))
        self.r.delete(0, END)
        self.r.insert(0, str(r))
        self.O.delete(0, END)
        self.O.insert(0, str(randint(-maxR, maxR)))
        self.n.delete(0, END)
        self.n.insert(0, str(int(abs(r / gcd(R, r)))))
        self.acc.set(int(abs(R/(r+0.1)/2))+1)

    def DrawSpiro(self, *args):
        try:
            R = int(self.R.get())
            r = int(self.r.get())
            n = int(self.n.get())
            O = int(self.O.get())
            acc = float(self.acc.get())
        except:
            self.CantDraw()
            printdebug("!!! EXCEPTION: Invalid format")
            return
        host = str(self.host.get())
        client(host, "{} {} {} {} {}".format(R, r, O, n, acc))

    def IdleTask(self):
        global OldPercentDone
        if PercentDone != OldPercentDone:
            OldPercentDone = PercentDone
            if PercentDone != 100: self.DrawPercent()
        self.PrintStatus()
        if not SpiroCoords.empty():
            coords = SpiroCoords.get()
            self.Visualize(coords)
        root.after(Tick, self.IdleTask)

    def DrawPercent(self):
        self.statusbar.delete(self.percent)
        if PercentDone: self.percent = self.statusbar.create_text(maxX-5, 0, text=str(PercentDone) + "%",
                                                                  fill = "black", anchor=NE)
        self.statusbar.update()
    
    def Visualize(self, coords):
        global PercentDone, OldPercentDone
        TimeBegin = time.time()
        PercentDone, OldPercentDone = 0, 0
        color = self.color.get()
        bg = self.bg.get()
        if color == bg:
            if color == "black": color = "white"
            else: color = "black"
        self.canvas.configure(background=bg)
        self.statusbar.delete(self.percent)
        self.vis = self.statusbar.create_text(maxX-5, 0, text="Visualization...", fill = "black", anchor=NE)
        self.statusbar.update()
        self.canvas.delete(self.line)
        try:
            if coords != None: self.line = self.canvas.create_line(coords, fill=color)
            else: raise
            self.canvas.update()
            TimeElapsed = time.time() - TimeBegin
            printdebug("*** Drew {0:,} lines in {1:.3f} sec".format(len(coords)-1, TimeElapsed))
        except:
            printdebug("!!! EXCEPTION: Can't draw")
            self.CantDraw()
        self.PrintC(bg)
        self.statusbar.delete(self.vis)
        self.statusbar.delete(self.percent)

    def CantDraw(self):
        color = self.color.get()
        bg = self.bg.get()
        if color == bg:
            if color == "black": color = "white"
            else: color = "black"
        self.canvas.configure(background=bg)
        self.canvas.delete(self.line)
        self.line = self.canvas.create_text(maxX/2, maxY/2, text="Can't draw this", fill=color)
        
    def PrintC(self, bg):
        self.canvas.create_text(maxX/2, maxY - 15, text = C + " 999Vulcan", fill="white" if bg == "black" else "black")

    def PrintStatus(self):
        threadcount = RunningThreads.qsize()
        queuesize = SpiroCoords.qsize()
        if (threadcount == self.threadcount) and (queuesize == self.queuesize): return
        self.statusbar.delete(self.status)
        self.threadcount = threadcount
        self.queuesize = queuesize
        if (threadcount > 0) or (queuesize > 0):
            self.status = self.statusbar.create_text(5, 0, text = "Threads: {0:<3}".format(threadcount) +
                                                     " Queue: {0:<3}".format(queuesize), fill = "black",
                                                     anchor=NW)
        self.statusbar.update()

def AbortThreads():
    global StopThreads
    printdebug("... Aborting {0} thread(s)".format(RunningThreads.qsize()))
    StopThreads = True
    while not RunningThreads.empty(): pass
    StopThreads = False
    printdebug("... Deleting {0} queued results".format(SpiroCoords.qsize()))
    while not SpiroCoords.empty(): SpiroCoords.get()
    
def Spirograph(*args):
    global SpiroCoords, PercentDone, OldPercentDone
    R, r, O, n, acc = args
    RunningThreads.put(None)
    printdebug(">>> Start Thread")
    coords = []
    precision = int(minPrec * acc)
    step = 2*pi/precision
    xoff, yoff = maxX/2, maxY/2
    oldx, oldy = None, None
    disc = 0
    oldpercent = -1
    PercentDone, OldPercentDone = 0, 0
    maxI = precision*n+1
    printdebug("+++ Computing {0:,} points".format(maxI))
    TimeBegin = time.time()
    try:
        Rr = R-r
        Rrr = Rr/r
        i = 0
        while i < maxI:
            t = i * step
            i += 1
            Rrrt = Rrr * t
            x = round(Rr*cos(t) + O*cos(Rrrt) + xoff)
            y = round(Rr*sin(t) - O*sin(Rrrt) + yoff)
            if (x != oldx) or (y != oldy):
                oldx, oldy = x, y
                coords.append((x, y))
            else: disc += 1
            if i % UpdateInterval > 0: continue
            percent = round(i/maxI*100)
            if oldpercent != percent:
                oldpercent = percent
                PercentDone = int(percent)
            if StopThreads:
                RunningThreads.get()
                printdebug("xxx Thread aborted")
                return
        TimeElapsed = time.time() - TimeBegin + 0.001
        printdebug("=== Stored {0:,}, discarded {1:,} pts in {2:.3f} sec: {3:,} pts/sec".format(
                   len(coords), disc, TimeElapsed, round(maxI/TimeElapsed)))
        SpiroCoords.put(coords)
    except:
        SpiroCoords.put(None)
        printdebug("!!! EXCEPTION: Can't compute")
    RunningThreads.get()
    printdebug("<<< Exit Thread")

def printdebug(*args):
    print(*args)

class ThreadedTCPRequestHandler(BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        try: data = str(data, 'ascii')
        except: pass
        R, r, O, n, acc = data.split()
        R = int(R)
        r = int(r)
        O = int(O)
        n = int(n)
        acc = float(acc)
        printdebug("Queued from {} R: {} r: {} O: {} n: {} acc: {}".format(self.request.getpeername(), R, r, O, n, acc))
        start_new_thread(Spirograph, (R, r, O, n, acc))

class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    pass

def client(host, message):
    try: message = bytes(message, 'ascii')
    except: pass

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(('localhost', port))
    
    try: sock.sendall(message)
    finally: sock.close()
    
    if host == 'localhost': return

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host, port))
    
    try: sock.sendall(message)
    finally: sock.close()

server = ThreadedTCPServer(("", port), ThreadedTCPRequestHandler)

server_thread = Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()

root = Tk()
resX = root.winfo_screenwidth()
resY = root.winfo_screenheight()
maxX = resX - 200
maxY = resY - 200
root.resizable(0, 0)
posX = 90
posY = int((resY - maxY)/2) - 50
root.geometry("+{}+{}".format(posX, posY))
app = App(root)
root.title('iSpirograph v. '+ version)
#root.tk_bisque()
i = sys.argv[0].rfind('\\')
try: root.iconbitmap(default=sys.argv[0][:i]+"\\spirograph.ico")
except: printdebug("Can't show window icon")

root.mainloop()

server.shutdown()
server.server_close()
