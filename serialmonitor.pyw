import serial
from tkinter import *
from tkinter import ttk
import threading
import queue

PORTS = ['COM3', 'COM4']
BAUDRATE = 2000000

class SerialManager:
    def __init__(self, port, baudrate, root):
        self._port = port
        self._baud = baudrate
        self.root = root
        self.send_queue = queue.Queue()
        self.msg_buffer = queue.Queue()
        self.ser = serial.Serial(self._port, self._baud)
        self.mutex = threading.Lock()
        self.exit_flag = threading.Event()
        self.msg_flag = threading.Event()
    @property
    def port(self):
        return self._port
    @port.setter
    def port(self, value):
        with self.mutex:
            self._port = value
            self.ser.port = value
    @property
    def baudrate(self):
        return self._baud
    @baudrate.setter
    def baudrate(self, value):
        with self.mutex:
            self._baud = value
            self.ser.baudrate = value

    def send(self, msg):
        self.send_queue.put(msg)
    def recv(self):
        msg = ''
        while True:
            try:
                msg += self.msg_buffer.get(False)
            except queue.Empty:
                return msg
    def exit(self):
        self.exit_flag.set()
    def loop(self):
        while not self.exit_flag.is_set():
            with self.mutex:
                recvmsg = self.ser.read_all()
            if len(recvmsg) > 0:
                recvmsg = str(recvmsg, 'ascii')
                with self.mutex:
                    self.msg_buffer.put(recvmsg)
                    self.msg_flag.set()
                self.root.event_generate(f'<<NEW>>')
                print(f"nwwwww{self.port}")
            if not self.send_queue.empty():
                sendmsg = self.send_queue.get()
                sendmsg = bytes(sendmsg, 'ascii')
                with self.mutex:
                    self.ser.write(sendmsg)

class WindowManager:
    def __init__(self, ports):
        self.ports = ports

        self.root = Tk()
        #self.mainframe = ttk.Frame(self.root)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(column=0, row=0)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.monitor_frame = {port: ttk.Frame(self.notebook) for port in ports}
        self.outbox = {port: Text(self.monitor_frame[port], state='disabled', width=140, height=40) for port in ports}
        self.inbox = {port: ttk.Entry(self.monitor_frame[port], textvariable=f"inbox{port}") for port in ports}
        self.send_button = {port: ttk.Button(self.monitor_frame[port], text="SEND", command=self.send_active) for port in ports}
        self.ser = {port: None for port in self.ports}
        self.text = {port: "" for port in self.ports}

        for port in ports:
            self.monitor_frame[port].grid(column=0, row=1, sticky=(N, W, E, S))
            self.outbox[port].grid(column=0,row=0, columnspan=10)
            self.inbox[port].grid(column=0, row=2, sticky=(W, E), columnspan=9)
            self.send_button[port].grid(column=9, row=2, sticky=(W,E))
            self.monitor_frame[port].bind(f"<<NEW>>", self.new_msg_bind(port), add=True)
            self.notebook.add(self.monitor_frame[port], text=port)
            print(port)
        self.root.bind("<Return>", lambda x: self.send_active())
        self.root.bind("<Destroy>", lambda x: [self.ser[port].exit() for port in self.ser])
        #self.root.bind("<<NotebookTabChanged>>", self.change_window)

        self.text = {port: "" for port in self.ports}

    def bind_serial(self, ser):
        self.ser = ser

    def send_active(self):
        port = self.ports[self.notebook.index(self.notebook.select())]
        self.send_msg(port)

    def mainloop(self):
        self.root.mainloop()

    def new_msg_bind(self, port):
        port = port
        def new_msg(e):
            ser = self.ser[port]
            msg = ser.recv()
            self.outbox[port]['state'] = 'normal'
            self.outbox[port].insert('end', msg)
            self.outbox[port]['state'] = 'disabled'
            self.text[port] += msg
        return new_msg
    
    def send_msg(self, port):
        msg = self.inbox[port].get()
        ser = self.ser[port]
        self.inbox[port].delete('0', 'end')
        ser.send(msg+'\n')
    
    #def change_window(self, event):
        #print(event)
        #new_window = self.active_window
        #self.outbox[port].delete("1.0", "end")
        #self.outbox[port].insert("1.0", self.text[new_window])
        #self.inbox[port].delete('0', 'end')
        #self.active_window = new_window


if __name__ == '__main__':
    window = WindowManager(PORTS)
    ser = {}
    thread = {}
    for port in PORTS:
        ser[port] = SerialManager(port, BAUDRATE, window.monitor_frame[port])
        thread[port] = threading.Thread(None, ser[port].loop)
        thread[port].start()
    print(ser)
    window.bind_serial(ser)
    window.mainloop()
