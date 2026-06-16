import sys
import threading
import random
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Import your existing script
import obs

class RedirectText(object):
    """Redirects console print statements to the Tkinter Text widget safely."""
    def __init__(self, text_widget, root):
        self.text_space = text_widget
        self.root = root

    def write(self, string):
        self.root.after(0, self._write, string)

    def _write(self, string):
        self.text_space.insert(tk.END, string)
        self.text_space.see(tk.END)
        
    def flush(self):
        pass


class StreamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OBS Cricket Stream Automation")
        self.root.geometry("650x550")
        self.root.configure(padx=10, pady=10)
        
        # Match ID Frame
        frame1 = ttk.Frame(root)
        frame1.pack(fill=tk.X, pady=5)
        ttk.Label(frame1, text="Match ID:", width=12).pack(side=tk.LEFT)
        self.match_id_var = tk.StringVar()
        self.match_id_entry = ttk.Entry(frame1, textvariable=self.match_id_var, width=25)
        self.match_id_entry.pack(side=tk.LEFT, padx=5)
        
        self.fetch_btn = ttk.Button(frame1, text="🔍 Fetch Title", command=self.start_fetch_thread)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        
        # Title Frame
        frame2 = ttk.Frame(root)
        frame2.pack(fill=tk.X, pady=5)
        ttk.Label(frame2, text="Stream Title:", width=12).pack(side=tk.LEFT)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(frame2, textvariable=self.title_var)
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Ground Frame
        frame3 = ttk.Frame(root)
        frame3.pack(fill=tk.X, pady=10)
        ttk.Label(frame3, text="Select Ground:", width=12).pack(side=tk.LEFT)
        self.ground_var = tk.StringVar(value="1")
        ttk.Radiobutton(frame3, text="Ground 1 (.111)", variable=self.ground_var, value="1").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(frame3, text="Ground 2 (.110)", variable=self.ground_var, value="2").pack(side=tk.LEFT, padx=10)
        
        # Go Live Button
        frame4 = ttk.Frame(root)
        frame4.pack(fill=tk.X, pady=10)
        self.go_live_btn = tk.Button(
            frame4, text="🚀 GO LIVE", bg="#d9534f", fg="white", 
            font=("Arial", 12, "bold"), relief="raised", command=self.start_stream_thread
        )
        self.go_live_btn.pack(fill=tk.X, ipady=5)
        
        # Log Output Frame
        frame5 = ttk.LabelFrame(root, text=" Automation Logs ")
        frame5.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(frame5, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Redirect stdout/stderr to the text widget
        sys.stdout = RedirectText(self.log_text, self.root)
        sys.stderr = RedirectText(self.log_text, self.root)
        
        print("✨ OBS Automation App Initialized. Enter a Match ID to begin.")

    def start_fetch_thread(self):
        match_id = self.match_id_var.get().strip()
        if not match_id:
            messagebox.showwarning("Input Required", "Please enter a Match ID first.")
            return
            
        self.fetch_btn.config(state=tk.DISABLED)
        self.go_live_btn.config(state=tk.DISABLED)
        print(f"\n🔍 Fetching details for match ID {match_id}...")
        
        # Run network requests in a background thread to keep UI responsive
        threading.Thread(target=self.fetch_title_worker, args=(match_id,), daemon=True).start()

    def fetch_title_worker(self, match_id):
        try:
            title = obs.fetch_stream_title(match_id)
            self.root.after(0, lambda: self.title_var.set(title))
            print(f"✅ Generated Stream Title: {title}")
        except Exception as e:
            print(f"⚠️ Error fetching title: {e}")
        finally:
            self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.go_live_btn.config(state=tk.NORMAL))

    def start_stream_thread(self):
        match_id = self.match_id_var.get().strip()
        stream_title = self.title_var.get().strip()
        ground_choice = self.ground_var.get()
        
        obs_port = 4566 if ground_choice == '1' else 4555

        if not match_id or not stream_title:
            messagebox.showwarning("Input Required", "Match ID and Stream Title are required to go live.")
            return
            
        self.go_live_btn.config(state=tk.DISABLED)
        self.fetch_btn.config(state=tk.DISABLED)
        
        # Run stream automation in a background thread
        threading.Thread(
            target=self.run_automation_worker, 
            args=(match_id, stream_title, ground_choice, obs_port), 
            daemon=True
        ).start()
        
    def run_automation_worker(self, match_id, stream_title, ground_choice, obs_port):
        try:
            print("\n=========================================")
            print("🚀 Starting Stream Automation Process...")
            print(f"🎯 Targeting OBS instance on port {obs_port}...")
            
            if not obs.check_obs_connection(port=obs_port):
                print("=========================================")
                return
            
            yt_service = obs.get_youtube_service()
            
            num_hashtags = random.randint(5, 10)
            selected_hashtags = random.sample(obs.CRICKET_MASTER_HASHTAGS, num_hashtags)
            stream_description = "Live cricket match broadcast!\n\n" + " ".join([f"#{tag}" for tag in selected_hashtags])
            print(f"📝 Generated Stream Description:\n{stream_description}\n")
            
            ticker_urls = [
                f"https://webticker.cricheroes.com/midnight-fire/{match_id}/",
                f"https://webticker.cricheroes.com/minimalist/{match_id}/",
                f"https://webticker.cricheroes.com/modern-edge/{match_id}/",
                f"https://webticker.cricheroes.com/bold-play/{match_id}/",
                f"https://webticker.cricheroes.com/crystal-view/{match_id}/",
                f"https://webticker.cricheroes.com/fresh-field/{match_id}/"
            ]
            ticker_url = random.choice(ticker_urls)
            print(f"🎲 Randomly selected Ticker URL: {ticker_url}")
            
            camera_url = "rtsp://admin:Admin@1508@192.168.0.111/Streaming/Channels/101/" if ground_choice == '1' else "rtsp://admin:Admin@1508@192.168.0.110/Streaming/Channels/101/"
                
            youtube_stream_key, broadcast_id = obs.create_youtube_broadcast(yt_service, stream_title, stream_description)
            obs.update_obs_and_stream(youtube_stream_key, ticker_url, camera_url, port=obs_port)
            
            print(f"\n▶️ Watch your live stream here: https://www.youtube.com/watch?v={broadcast_id}")
            print("=========================================")
        except Exception as e:
            print(f"💥 Script failed: {e}")
        finally:
            self.root.after(0, lambda: self.go_live_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = StreamApp(root)
    root.mainloop()