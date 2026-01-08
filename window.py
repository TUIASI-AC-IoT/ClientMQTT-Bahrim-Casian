import tkinter as tk
import communication_controller as comm

color = "#71C4FF"
class Window(tk.Tk):
    def __init__(self, height, width):
        super().__init__()
        self.title("Client MQTT")
        self.geometry(f"{width}x{height}")
        self.resizable(False,False)
        self.config(padx=50, pady=50, bg=color)
        self.host = None
        self.port = None
        self.client_id = None

        # User Frame
        self.user_frame = tk.LabelFrame(self, text="User", bg=color, padx=5, pady=5, font=("Arial", 14))
        self.user_frame.grid(row=0, column=0, padx=10, pady=(10,20), sticky="nw")

        tk.Label(self.user_frame, text="ID Client:",bg=color,font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=10)
        self.client_id_entry=tk.Entry(self.user_frame)
        self.client_id_entry.insert(0, "")
        self.client_id_entry.grid(row=2,column=1,padx=10,pady=10)

        tk.Label(self.user_frame, text="Username: ",bg=color,font=("Arial", 12)).grid(row=3, column=0, padx=10, pady=10)
        self.username_entry=tk.Entry(self.user_frame)
        self.username_entry.insert(0,"")
        self.username_entry.grid(row=3,column=1,padx=10,pady=10)

        tk.Label(self.user_frame, text="Password: ",bg=color,font=("Arial", 12)).grid(row=4, column=0, padx=10, pady=10)
        self.password_entry=tk.Entry(self.user_frame, show="*")
        self.password_entry.insert(0,"")
        self.password_entry.grid(row=4,column=1,padx=10,pady=10)

        tk.Label(self.user_frame, text="Will Topic: ",bg=color,font=("Arial", 12)).grid(row=5, column=0, padx=10, pady=10)
        self.will_topic_entry=tk.Entry(self.user_frame)
        self.will_topic_entry.insert(0,"")
        self.will_topic_entry.grid(row=5,column=1,padx=10,pady=10)

        tk.Label(self.user_frame, text="Will Message: ",bg=color,font=("Arial", 12)).grid(row=6, column=0, padx=10, pady=10)
        self.will_message_entry=tk.Entry(self.user_frame)
        self.will_message_entry.insert(0,"")
        self.will_message_entry.grid(row=6,column=1,padx=10,pady=10)

        tk.Label(self.user_frame, text="Will QoS: ",bg=color,font=("Arial", 12)).grid(row=7, column=0, padx=10, pady=10)
        self.will_qos_var = tk.StringVar(value="0")
        self.will_qos_menu = tk.OptionMenu(self.user_frame, self.will_qos_var, "0", "1", "2")
        self.will_qos_menu.grid(row=7, column=1, padx=10, pady=10)

        # Broker Frame
        self.broker_frame = tk.LabelFrame(self, text="Broker", bg=color, padx=5, pady=5, font=("Arial", 14))
        self.broker_frame.grid(row=0, column=1, padx=10, pady=(10,20), sticky="ne")

        tk.Label(self.broker_frame, text="Host:",bg=color,font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=10)
        self.host_entry=tk.Entry(self.broker_frame)
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.grid(row=2,column=1,padx=10,pady=10)

        tk.Label(self.broker_frame, text="Port: ",bg=color,font=("Arial", 12)).grid(row=3, column=0, padx=10, pady=10)
        self.port_entry=tk.Entry(self.broker_frame)
        self.port_entry.insert(0,"1884")
        self.port_entry.grid(row=3,column=1,padx=10,pady=10)


        port = int(self.port_entry.get())
        will_qos = int(self.will_qos_var.get())
        self.comm = comm.CommunicationController(self.host_entry.get(), port)

        self.connect_button=tk.Button(self, text="  Connect  ",font=("Arial", 12,"bold"), bg="#0052CD",fg="white",padx=10, pady=6, 
                            command=lambda: (self.comm.connect_to_server(self.client_id_entry.get(),
                            self.username_entry.get(), self.password_entry.get(), self.will_topic_entry.get(), self.will_message_entry.get(), will_qos)))
        self.connect_button.grid(row=1,column=0,columnspan=1,pady=(8,0),sticky="ew") 

        self.disconnect_button=tk.Button(self, text=" Disconnect ",font=("Arial", 12,"bold"), bg="#0052CD",fg="white",padx=10, pady=6,
                            command=lambda: (self.comm.disconnect()))
        self.disconnect_button.grid(row=1,column=1,columnspan=1,pady=(8,0),sticky="ew")

        self.publish_button=tk.Button(self, text="  Publish  ",font=("Arial", 12,"bold"), bg="#0052CD",fg="white",padx=10, pady=6,command=lambda: (publish_window()))
        self.publish_button.grid(row=2,column=1,columnspan=1,pady=(8,0),sticky="ew")
            

        self.subscribe_button=tk.Button(self, text=" Subscribe ",font=("Arial", 12,"bold"), bg="#0052CD",fg="white",padx=10, pady=6,command=lambda: (subscribe_window()))
        self.subscribe_button.grid(row=2,column=0,columnspan=1,pady=(8,0),sticky="ew")

        def publish_window():
            pub_win = tk.Toplevel(self)
            pub_win.title("Publish Message")
            pub_win.geometry("400x300")
            pub_win.resizable(False,False)
            pub_win.config(padx=20, pady=20, bg=color)

            tk.Label(pub_win, text="Topic:",bg=color,font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
            topic_var = tk.StringVar(value="CPU Frequency")
            topic_menu=tk.OptionMenu(pub_win, topic_var, "CPU Frequency", "CPU Usage", "Memory Usage")
            topic_menu.grid(row=0,column=1,padx=10,pady=10)


            tk.Label(pub_win, text="QoS: ",bg=color,font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10)
            qos_var = tk.StringVar(value="0")
            qos_menu = tk.OptionMenu(pub_win, qos_var, "0", "1", "2")
            qos_menu.grid(row=1, column=1, padx=10, pady=10)

            def send_publish():
                topic_message = topic_var.get()
                qos = int(qos_var.get())
                self.comm.publish_message(topic_message, qos)

            send_button=tk.Button(pub_win, text="  Send  ",font=("Arial", 12,"bold"), bg="#0052CD",fg="white",padx=10, pady=6,
                                command=lambda :send_publish())
            send_button.grid(row=2,column=0,columnspan=2,pady=(8,0),sticky="ew")

        def subscribe_window():
            sub_win = tk.Toplevel(self)
            sub_win.title("Subscribe to Topic")
            sub_win.geometry("400x400")
            sub_win.resizable(False,False)
            sub_win.config(padx=20, pady=20, bg=color)

            sub_win.grid_columnconfigure(0, weight=0)
            sub_win.grid_columnconfigure(1, weight=1)
            sub_win.grid_columnconfigure(2, weight=1)

            tk.Label(sub_win, text="Topic:",bg=color,font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
            topic_var = tk.StringVar(value="CPU Frequency")
            topic_menu=tk.OptionMenu(sub_win, topic_var, "CPU Frequency", "CPU Usage", "Memory Usage")
            topic_menu.grid(row=0,column=1,padx=10,pady=10)

            tk.Label(sub_win, text="QoS: ",bg=color,font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10)
            qos_var = tk.StringVar(value="0")
            qos_menu = tk.OptionMenu(sub_win, qos_var, "0", "1", "2")
            qos_menu.grid(row=1, column=1, padx=10, pady=10)

            tk.Label(sub_win, text="Message:", bg=color, font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=10, sticky="w")

            textbox = tk.Text(sub_win, height=5, width=10)
            textbox.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")        

            def send_subscribe():
                topic_message = topic_var.get()
                qos = int(qos_var.get())
                self.comm.subscribe_topic(topic_message, qos)
        
            send_button=tk.Button(sub_win, text=" Subscribe ",font=("Arial", 12,"bold"), bg="#0052CD",fg="white",padx=10, pady=6,
                                command=lambda :send_subscribe())
            send_button.grid(row=3,column=0,columnspan=2,pady=(8,0),sticky="ew")    
            
            unsub_button=tk.Button(sub_win, text=" Unsubscribe ",font=("Arial", 12,"bold"), bg="#0052CD",fg="white",padx=10, pady=6,
                                command=lambda :self.comm.unsubscribe_topic(topic_var.get()))
            unsub_button.grid(row=4,column=0,columnspan=2,pady=(8,0),sticky="ew")

            
            def update_textbox():
                if self.comm.received_message is not None:
                    textbox.insert(tk.END, f"{self.comm.received_topic}: {self.comm.received_message}\n")
                    textbox.see(tk.END)
                    self.comm.received_message = None
                sub_win.after(200, update_textbox)

            update_textbox()
            
            
window = Window(500, 650)
window.mainloop()