import random
import time
import datetime
import mysql.connector
import tkinter as tk
from tkinter import messagebox
import os

class Minesweeper:
    def __init__(self, rows, cols, num_mines):
        self.rows, self.cols, self.num_mines = rows, cols, num_mines
        self.board = [[' ' for _ in range(cols)] for _ in range(rows)]
        self.mine_locations = random.sample(range(rows * cols), num_mines)
        self.revealed_cells = [[False] * cols for _ in range(rows)]
        self.flagged_cells = [[False] * cols for _ in range(rows)]
        self.questioned_cells = [[False] * cols for _ in range(rows)]  # NEW: Question mark state
        self.start_time = None
        self.place_mines()
        self.calculate_adjacent_mines()
        try:
            self.conn = mysql.connector.connect(
                host='localhost', 
                user='root', 
                passwd='4589', 
                database='minesweeper_leaderboard'
            )
            cursor = self.conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTO_INCREMENT, 
                player_name TEXT, 
                elapsed_time REAL, 
                game_won BOOLEAN, 
                difficulty_mode TEXT, 
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )''')
            self.conn.commit()
            cursor.close()
            print("Database connection established successfully")
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            print("Game will continue without leaderboard functionality")
            self.conn = None
        except Exception as e:
            print(f"Unexpected error during database setup: {e}")
            self.conn = None

    def place_mines(self):
        for loc in self.mine_locations:
            row, col = divmod(loc, self.cols)
            self.board[row][col] = '💣'

    def calculate_adjacent_mines(self):
        directions = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
        for loc in self.mine_locations:
            row, col = divmod(loc, self.cols)
            for i, j in directions:
                nr, nc = row + i, col + j
                if 0 <= nr < self.rows and 0 <= nc < self.cols and self.board[nr][nc] != '💣':
                    self.board[nr][nc] = '1' if self.board[nr][nc] == ' ' else str(int(self.board[nr][nc]) + 1)

    def reveal_cell(self, row, col):
        if self.flagged_cells[row][col] or self.questioned_cells[row][col] or self.revealed_cells[row][col]:
            return None
        self.revealed_cells[row][col] = True
        if self.start_time is None:
            self.start_time = time.time()
        if (row * self.cols + col) in self.mine_locations:
            return False
        if self.board[row][col] == ' ':
            self.board[row][col] = '0'
            self.reveal_empty_cells(row, col)
        return True

    def reveal_empty_cells(self, row, col):
        for i, j in [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]:
            nr, nc = row + i, col + j
            if 0 <= nr < self.rows and 0 <= nc < self.cols and not self.revealed_cells[nr][nc]:
                self.revealed_cells[nr][nc] = True
                if (nr * self.cols + nc) not in self.mine_locations and self.board[nr][nc] == ' ':
                    self.board[nr][nc] = '0'
                    self.reveal_empty_cells(nr, nc)

    def cycle_flag(self, row, col):
        """NEW: Cycle through unmarked -> flag -> question mark -> unmarked"""
        if not self.revealed_cells[row][col]:
            if not self.flagged_cells[row][col] and not self.questioned_cells[row][col]:
                # Unmarked -> Flag
                self.flagged_cells[row][col] = True
            elif self.flagged_cells[row][col]:
                # Flag -> Question mark
                self.flagged_cells[row][col] = False
                self.questioned_cells[row][col] = True
            else:
                # Question mark -> Unmarked
                self.questioned_cells[row][col] = False
            return True
        return False

    def get_elapsed_time(self):
        return time.time() - self.start_time if self.start_time else 0

    def check_win(self):
        return all(self.revealed_cells[i][j] or (i * self.cols + j) in self.mine_locations 
                   for i in range(self.rows) for j in range(self.cols))

    def update_leaderboard(self, player_name, elapsed_time, game_won, difficulty_mode, play_date):
        if game_won and self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''INSERT INTO leaderboard (player_name, elapsed_time, game_won, difficulty_mode, timestamp)
                                  VALUES (%s, %s, %s, %s, %s)''', 
                              (player_name, round(elapsed_time, 2), 1, difficulty_mode, play_date))
                self.conn.commit()
                cursor.close()
                print(f"Leaderboard updated for {player_name}")
            except mysql.connector.Error as e:
                print(f"Database error while updating leaderboard: {e}")
            except Exception as e:
                print(f"Unexpected error while updating leaderboard: {e}")

    def __del__(self):
        """Properly close database connection when object is destroyed"""
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
                print("Database connection closed")
            except Exception as e:
                print(f"Error closing database connection: {e}")


class MinesweeperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minesweeper")
        self.root.configure(bg="#000000")
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', True))
        self.game = None
        self.buttons = []
        self.player_name = ""
        self.difficulty_mode = ""
        self.timer_label = None
        self.timer_running = False
        self.show_splash_screen()

    def create_button(self, parent, text, font_size, command):
        return tk.Button(parent, text=text, font=("Arial", font_size), bg="#1a1a1a", fg="#ffffff",
                        activebackground="#2a2a2a", activeforeground="#00ff88", bd=0,
                        padx=30 if font_size >= 20 else 25, pady=10 if font_size >= 20 else 8,
                        cursor="hand2", command=command)

    def show_main_menu(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#000000")
        frame.pack(expand=True)
        tk.Label(frame, text="MINESWEEPER", font=("Arial", 64, "bold"), bg="#000000", fg="#00ff88").pack(pady=60)
        self.create_button(frame, "START GAME", 20, self.show_name_input).pack(pady=20)
        self.create_button(frame, "LEADERBOARD", 20, self.show_leaderboard).pack(pady=20)
        self.create_button(frame, "EXIT", 20, self.root.quit).pack(pady=20)
        tk.Label(frame, text="Press ESC to exit fullscreen | F11 to enter fullscreen",
                font=("Arial", 10), bg="#000000", fg="#555555").pack(pady=40)

    def show_name_input(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#000000")
        frame.pack(expand=True)
        tk.Label(frame, text="ENTER YOUR NAME", font=("Arial", 42, "bold"), bg="#000000", fg="#00ff88").pack(pady=60)
        name_entry = tk.Entry(frame, font=("Arial", 24), bg="#1a1a1a", fg="#ffffff", insertbackground="#00ff88", bd=0, relief="flat")
        name_entry.pack(pady=30, ipady=15, ipadx=30)
        name_entry.focus()
        
        def on_continue():
            if name_entry.get().strip():
                self.player_name = name_entry.get().strip()
                self.show_difficulty_selection()
            else:
                messagebox.showwarning("Warning", "Please enter your name!")
        
        self.create_button(frame, "CONTINUE", 20, on_continue).pack(pady=30)
        self.create_button(frame, "BACK", 16, self.show_main_menu).pack(pady=15)
        name_entry.bind('<Return>', lambda e: on_continue())

    def show_difficulty_selection(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#000000")
        frame.pack(expand=True)
        tk.Label(frame, text="CHOOSE DIFFICULTY", font=("Arial", 42, "bold"), bg="#000000", fg="#00ff88").pack(pady=60)
        for text, mines, diff in [("EASY (5 Mines)", 5, "Easy"), ("MEDIUM (8 Mines)", 8, "Medium"), ("HARD (12 Mines)", 12, "Hard")]:
            self.create_button(frame, text, 20, lambda m=mines, d=diff: self.start_game(m, d)).pack(pady=20)
        self.create_button(frame, "BACK", 16, self.show_main_menu).pack(pady=30)

    def start_game(self, num_mines, difficulty):
        self.difficulty_mode = difficulty
        self.game = Minesweeper(10, 10, num_mines)
        self.show_game_board()

    def show_game_board(self):
        self.clear_window()
        self.timer_running = True
        top_frame = tk.Frame(self.root, bg="#000000")
        top_frame.pack(pady=30)
        tk.Label(top_frame, text=f"Player: {self.player_name} | Difficulty: {self.difficulty_mode}",
                font=("Arial", 18), bg="#000000", fg="#00ff88").pack()
        self.timer_label = tk.Label(top_frame, text="Time: 0.00s", font=("Arial", 20, "bold"), bg="#000000", fg="#ffffff")
        self.timer_label.pack(pady=15)
        # UPDATED: Added question mark instruction
        tk.Label(top_frame, text="Left Click: Reveal | Right Click: Flag/Question Mark", 
                font=("Arial", 14), bg="#000000", fg="#666666").pack()
        
        game_frame = tk.Frame(self.root, bg="#000000", padx=20, pady=20)
        game_frame.pack()
        self.buttons = []
        for i in range(10):
            row_buttons = []
            for j in range(10):
                btn = tk.Button(game_frame, text="", width=4, height=2, font=("Arial", 12, "bold"),
                               bg="#1a1a1a", fg="#ffffff", activebackground="#2a2a2a", bd=1, relief="raised", cursor="hand2")
                btn.grid(row=i, column=j, padx=2, pady=2)
                btn.bind('<Button-1>', lambda e, r=i, c=j: self.on_cell_click(r, c))
                btn.bind('<Button-3>', lambda e, r=i, c=j: self.on_cell_right_click(r, c))
                row_buttons.append(btn)
            self.buttons.append(row_buttons)
        
        button_frame = tk.Frame(self.root, bg="#000000")
        button_frame.pack(pady=30)
        self.create_button(button_frame, "BACK TO MENU", 16, 
                          lambda: self.show_main_menu() if messagebox.askyesno("Confirm", "Exit game?") else None).pack()
        
        self.update_timer()

    def update_timer(self):
        if self.timer_running and self.game:
            self.timer_label.config(text=f"Time: {self.game.get_elapsed_time():.2f}s")
            self.root.after(100, self.update_timer)

    def on_cell_click(self, row, col):
        if not self.game:
            return
        result = self.game.reveal_cell(row, col)
        if result is not None:
            self.update_board()
            if result:
                if self.game.check_win():
                    self.timer_running = False
                    elapsed = self.game.get_elapsed_time()
                    self.game.update_leaderboard(self.player_name, elapsed, True, self.difficulty_mode, 
                                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    messagebox.showinfo("Victory!", f"You Won!\nTime: {elapsed:.2f}s")
                    self.show_main_menu()
            else:
                self.timer_running = False
                self.reveal_all_mines()
                messagebox.showinfo("Game Over", f"You hit a mine!\nTime: {self.game.get_elapsed_time():.2f}s")
                self.show_main_menu()

    def on_cell_right_click(self, row, col):
        # UPDATED: Use cycle_flag instead of toggle_flag
        if self.game and self.game.cycle_flag(row, col):
            self.update_board()

    def update_board(self):
        colors = {'1': '#00d4ff', '2': '#00ff88', '3': '#ff6b6b', '4': '#ffd93d', 
                  '5': '#ff8800', '6': '#00ffff', '7': '#ff00ff', '8': '#ff0000'}
        for i in range(10):
            for j in range(10):
                if self.game.revealed_cells[i][j]:
                    val = self.game.board[i][j]
                    self.buttons[i][j].config(text=val, bg="#0a0a0a", relief="sunken", state="disabled", fg=colors.get(val, '#ffffff'))
                elif self.game.flagged_cells[i][j]:
                    self.buttons[i][j].config(text="🚩", bg="#1a1a1a", fg="#ff0000")
                elif self.game.questioned_cells[i][j]:  # NEW: Show question mark
                    self.buttons[i][j].config(text="❓", bg="#1a1a1a", fg="#ffd93d")
                else:
                    self.buttons[i][j].config(text="", bg="#1a1a1a")

    def reveal_all_mines(self):
        for i in range(10):
            for j in range(10):
                if (i * self.game.cols + j) in self.game.mine_locations:
                    self.buttons[i][j].config(text="💣", bg="#ff0000", state="disabled")

    def show_leaderboard(self):
        self.clear_window()
        main_frame = tk.Frame(self.root, bg="#000000")
        main_frame.pack(expand=True, fill="both")
        title_frame = tk.Frame(main_frame, bg="#000000")
        title_frame.pack(pady=40)
        tk.Label(title_frame, text="🏆 LEADERBOARD 🏆", font=("Arial", 48, "bold"), bg="#000000", fg="#00ff88").pack()
        tk.Label(title_frame, text="Top Players - Fastest Times", font=("Arial", 16), bg="#000000", fg="#666666").pack(pady=10)
        
        canvas_frame = tk.Frame(main_frame, bg="#000000")
        canvas_frame.pack(expand=True, fill="both", padx=100, pady=20)
        canvas = tk.Canvas(canvas_frame, bg="#000000", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview, bg="#1a1a1a", troughcolor="#000000", width=20)
        scrollable_frame = tk.Frame(canvas, bg="#000000")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        header_frame = tk.Frame(scrollable_frame, bg="#1a1a1a", height=60)
        header_frame.pack(fill="x", padx=20, pady=(0, 10))
        for text, color, width, anchor in [("RANK", "#FFD700", 8, "center"), ("PLAYER", "#00d4ff", 19, "w"), 
                                            ("TIME", "#00ff88", 11, "w"), ("DIFFICULTY", "#ff6b6b", 17, "w"), 
                                            ("DATE", "#ffd93d", 20, "w")]:
            tk.Label(header_frame, text=text, font=("Times New Roman", 14, "bold"), bg="#1a1a1a", fg=color, width=width, anchor=anchor).pack(side="left", padx=20, pady=15)
        
        try:
            conn = mysql.connector.connect(
                host='localhost', 
                user='root', 
                passwd='4589', 
                database='minesweeper_leaderboard'
            )
            cursor = conn.cursor()
            cursor.execute('SELECT player_name, elapsed_time, difficulty_mode, timestamp FROM leaderboard ORDER BY elapsed_time LIMIT 50')
            rows = cursor.fetchall()
            colors = ["#2a2a2a", "#1a1a1a"]
            rank_colors = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}
            diff_colors = {"Easy": "#00ff88", "Medium": "#ffd93d", "Hard": "#ff6b6b"}
            
            for idx, row in enumerate(rows, 1):
                row_frame = tk.Frame(scrollable_frame, bg=colors[idx % 2], height=50)
                row_frame.pack(fill="x", padx=20, pady=2)
                rank_text = f"#{idx}" if idx > 3 else ["🥇", "🥈", "🥉"][idx-1]
                rank_font_size = 18  
                tk.Label(row_frame, text=rank_text, font=("Arial", rank_font_size, "bold"), bg=colors[idx % 2], 
                        fg=rank_colors.get(idx, "#ffffff"), width=6, anchor="center").pack(side="left", padx=20, pady=12)
                tk.Label(row_frame, text=row[0], font=("Arial", 13), bg=colors[idx % 2], fg= "#00d4ff", width=17, anchor="w").pack(side="left", padx=20, pady=12)
                tk.Label(row_frame, text=f"{row[1]:.2f}s", font=("Arial", 16, "bold"), bg=colors[idx % 2], fg="#00ff88", width=12, anchor="center").pack(side="left", padx=20, pady=12)
                tk.Label(row_frame, text=row[2], font=("Arial", 13, "bold"), bg=colors[idx % 2], fg=diff_colors.get(row[2], "#ffffff"), width=15, anchor="center").pack(side="left", padx=20, pady=12)
                tk.Label(row_frame, text=str(row[3]), font=("Arial", 11, "bold"), bg=colors[idx % 2], fg="#ffd93d", width=20, anchor="center").pack(side="left", padx=20, pady=12)
            
            if not rows:
                tk.Label(scrollable_frame, text="No records yet. Be the first to play!", font=("Arial", 18), bg="#000000", fg="#666666").pack(pady=50)
            cursor.close()
            conn.close()
        except mysql.connector.Error as e:
            error_msg = f"Database connection error: {str(e)}"
            print(error_msg)
            tk.Label(scrollable_frame, text=f"Could not load leaderboard\n{error_msg}", 
                    font=("Arial", 16), bg="#000000", fg="#ff6b6b").pack(pady=50)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            tk.Label(scrollable_frame, text=f"Could not load leaderboard\n{error_msg}", 
                    font=("Arial", 16), bg="#000000", fg="#ff6b6b").pack(pady=50)
        
        button_frame = tk.Frame(main_frame, bg="#000000")
        button_frame.pack(pady=30)
        self.create_button(button_frame, "BACK TO MENU", 18, self.show_main_menu).pack()

    def show_splash_screen(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#000000")
        frame.pack(expand=True, fill="both")
        
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            self.logo_photo = tk.PhotoImage(file=logo_path)
            logo_label = tk.Label(frame, image=self.logo_photo, bg="#000000", cursor="hand2")
            logo_label.pack(expand=True)
            logo_label.bind("<Button-1>", lambda e: self.show_main_menu())
            logo_label.focus_set()
            frame.bind("<Button-1>", lambda e: self.show_main_menu())
        except FileNotFoundError:
            print("Warning: logo.png not found. Skipping splash screen.")
            self.show_main_menu()
        except Exception as e:
            print(f"Error loading splash screen: {e}")
            self.show_main_menu()

    def clear_window(self):
        self.timer_running = False
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    MinesweeperGUI(root)
    root.mainloop()
