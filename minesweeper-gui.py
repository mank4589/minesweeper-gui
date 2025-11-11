import random
import time
import datetime
import mysql.connector
import tkinter as tk
from tkinter import messagebox, ttk

class Minesweeper:
    def __init__(self, rows, cols, num_mines):
        self.rows, self.cols, self.num_mines = rows, cols, num_mines
        self.board = [[' ' for _ in range(cols)] for _ in range(rows)]
        self.mine_locations = []
        self.revealed_cells = [[False] * cols for _ in range(rows)]
        self.flagged_cells = [[False] * cols for _ in range(rows)]
        self.place_mines()
        self.calculate_adjacent_mines()
        self.start_time = None
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            passwd='4589',
            database='minesweeper_leaderboard'
        )
        self.create_leaderboard_table()

    def create_leaderboard_table(self):
        cursor = self.conn.cursor()
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                player_name TEXT,
                elapsed_time REAL,
                difficulty_mode TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                game_won BOOLEAN DEFAULT FALSE)''')
        self.conn.commit()

    def place_mines(self):
        self.mine_locations = random.sample(range(self.rows * self.cols), self.num_mines)
        for loc in self.mine_locations:
            row, col = divmod(loc, self.cols)
            self.board[row][col] = '💣'

    def calculate_adjacent_mines(self):
        directions = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
        for loc in self.mine_locations:
            row, col = divmod(loc, self.cols)
            for i, j in directions:
                new_row, new_col = row + i, col + j
                if 0 <= new_row < self.rows and 0 <= new_col < self.cols and self.board[new_row][new_col] != '💣':
                    if self.board[new_row][new_col] == ' ':
                        self.board[new_row][new_col] = '1'
                    else:
                        self.board[new_row][new_col] = str(int(self.board[new_row][new_col]) + 1)

    def reveal_cell(self, row, col):
        if self.flagged_cells[row][col]:
            return None
        if not self.revealed_cells[row][col]:
            self.revealed_cells[row][col] = True
            if self.start_time is None:
                self.start_time = time.time()
            if (row * self.cols + col) in self.mine_locations:
                return False
            elif self.board[row][col] == ' ':
                self.board[row][col] = '0'
                self.reveal_empty_cells(row, col)
            return True
        return None

    def reveal_empty_cells(self, row, col):
        directions = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if i != 0 or j != 0]
        for i, j in directions:
            new_row, new_col = row + i, col + j
            if 0 <= new_row < self.rows and 0 <= new_col < self.cols and not self.revealed_cells[new_row][new_col]:
                self.revealed_cells[new_row][new_col] = True
                if (new_row * self.cols + new_col) not in self.mine_locations and self.board[new_row][new_col] == ' ':
                    self.board[new_row][new_col] = '0'
                    self.reveal_empty_cells(new_row, new_col)

    def toggle_flag(self, row, col):
        if not self.revealed_cells[row][col]:
            self.flagged_cells[row][col] = not self.flagged_cells[row][col]
            return True
        return False

    def get_elapsed_time(self):
        if self.start_time is not None:
            return time.time() - self.start_time
        return 0

    def check_win(self):
        for i in range(self.rows):
            for j in range(self.cols):
                if (i * self.cols + j) not in self.mine_locations and not self.revealed_cells[i][j]:
                    return False
        return True

    def update_leaderboard(self, player_name, elapsed_time, game_won, difficulty_mode, play_date):
        if game_won:
            try:
                query = '''INSERT INTO leaderboard (player_name, elapsed_time, game_won, difficulty_mode, timestamp)
                    VALUES (%s, %s, %s, %s, %s)'''
                values = (player_name, round(elapsed_time, 2), 1, difficulty_mode, play_date)
                cursor = self.conn.cursor()
                cursor.execute(query, values)
                self.conn.commit()
                cursor.close()
            except Exception as e:
                print(f"Error updating leaderboard: {e}")


class MinesweeperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minesweeper")
        self.root.geometry("650x750")
        self.root.configure(bg='#0a0e27')
        
        self.game = None
        self.buttons = []
        self.player_name = ""
        self.difficulty_mode = ""
        self.timer_label = None
        self.timer_running = False
        
        # Dark theme colors
        self.bg_primary = '#0a0e27'
        self.bg_secondary = '#1a1f3a'
        self.bg_card = '#252b48'
        self.accent_blue = '#00d4ff'
        self.accent_purple = '#b24bf3'
        self.accent_green = '#00ff88'
        self.text_primary = '#ffffff'
        self.text_secondary = '#8b92b0'
        
        self.colors = {
            '0': '#4a5568',
            '1': '#00d4ff',
            '2': '#00ff88',
            '3': '#ff3e6c',
            '4': '#b24bf3',
            '5': '#ffa500',
            '6': '#00fff5',
            '7': '#ff6b9d',
            '8': '#ffdd00'
        }
        
        self.show_main_menu()

    def show_main_menu(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg=self.bg_primary)
        frame.pack(expand=True)
        
        # Title with gradient effect simulation
        title_frame = tk.Frame(frame, bg=self.bg_primary)
        title_frame.pack(pady=40)
        
        title = tk.Label(title_frame, text="💣 MINESWEEPER", font=('Arial', 40, 'bold'), 
                        bg=self.bg_primary, fg=self.accent_blue)
        title.pack()
        
        
        
        # Menu buttons with hover effect
        btn_frame = tk.Frame(frame, bg=self.bg_primary)
        btn_frame.pack(pady=30)
        
        buttons_config = [
            ("🎮 Start Game", self.show_player_input, self.accent_blue),
            ("🏆 Display Records", self.show_leaderboard, self.accent_purple),
            ("❌ Exit Game", self.root.quit, '#ff3e6c')
        ]
        
        for text, command, color in buttons_config:
            btn = tk.Button(btn_frame, text=text, command=command,
                           font=('Arial', 16, 'bold'), width=22, height=2,
                           bg=self.bg_card, fg=color, relief='flat',
                           bd=0, cursor='hand2', activebackground=self.bg_secondary,
                           activeforeground=color)
            btn.pack(pady=12)
            self.add_hover_effect(btn, color)

    def add_hover_effect(self, button, color):
        """Add hover effect to buttons"""
        def on_enter(e):
            button.config(bg=self.bg_secondary, fg=self.text_primary)
        
        def on_leave(e):
            button.config(bg=self.bg_card, fg=color)
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)

    def show_player_input(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg=self.bg_primary)
        frame.pack(expand=True)
        
        # Card container
        card = tk.Frame(frame, bg=self.bg_card, relief='flat', bd=0)
        card.pack(padx=40, pady=40)
        
        tk.Label(card, text="👤 Enter Your Name", font=('Arial', 24, 'bold'), 
                bg=self.bg_card, fg=self.text_primary).pack(pady=30, padx=60)
        
        entry_frame = tk.Frame(card, bg=self.bg_card)
        entry_frame.pack(pady=20, padx=60)
        
        name_entry = tk.Entry(entry_frame, font=('Arial', 16), width=25,
                             bg=self.bg_secondary, fg=self.text_primary,
                             insertbackground=self.accent_blue, relief='flat',
                             bd=0, highlightthickness=2, highlightbackground=self.bg_secondary,
                             highlightcolor=self.accent_blue)
        name_entry.pack(ipady=10)
        name_entry.focus()
        
        def submit_name():
            self.player_name = name_entry.get().strip()
            if self.player_name:
                self.show_difficulty_menu()
            else:
                messagebox.showwarning("Warning", "Please enter your name!")
        
        btn_frame = tk.Frame(card, bg=self.bg_card)
        btn_frame.pack(pady=30, padx=60)
        
        continue_btn = tk.Button(btn_frame, text="Continue →", command=submit_name,
                                font=('Arial', 14, 'bold'), width=15, height=2,
                                bg=self.bg_secondary, fg=self.accent_green, relief='flat',
                                bd=0, cursor='hand2')
        continue_btn.pack(pady=8)
        self.add_hover_effect(continue_btn, self.accent_green)
        
        back_btn = tk.Button(btn_frame, text="← Back", command=self.show_main_menu,
                            font=('Arial', 14, 'bold'), width=15, height=2,
                            bg=self.bg_secondary, fg=self.text_secondary, relief='flat',
                            bd=0, cursor='hand2')
        back_btn.pack(pady=8)
        self.add_hover_effect(back_btn, self.text_secondary)
        
        name_entry.bind('<Return>', lambda e: submit_name())

    def show_difficulty_menu(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg=self.bg_primary)
        frame.pack(expand=True)
        
        tk.Label(frame, text="⚙️ Choose Difficulty", font=('Arial', 28, 'bold'), 
                bg=self.bg_primary, fg=self.text_primary).pack(pady=40)
        
        difficulties = [
            ("🟢 EASY", "5 mines · Perfect for beginners", 5, 'Easy', self.accent_green),
            ("🟡 MEDIUM", "8 mines · Moderate challenge", 8, 'Medium', '#ffa500'),
            ("🔴 HARD", "12 mines · Expert level", 12, 'Hard', '#ff3e6c')
        ]
        
        for title, subtitle, mines, mode, color in difficulties:
            card = tk.Frame(frame, bg=self.bg_card, relief='flat', bd=0)
            card.pack(pady=10, padx=60, fill='x')
            
            btn = tk.Button(card, text=title, command=lambda m=mines, d=mode: self.start_game(m, d),
                           font=('Arial', 18, 'bold'), bg=self.bg_card, fg=color,
                           relief='flat', bd=0, cursor='hand2', anchor='w', padx=30, pady=15)
            btn.pack(fill='x')
            
            tk.Label(card, text=subtitle, font=('Arial', 11), bg=self.bg_card, 
                    fg=self.text_secondary, anchor='w', padx=30).pack(fill='x', pady=(0, 10))
            
            self.add_hover_effect(btn, color)
        
        back_btn = tk.Button(frame, text="← Back to Main Menu", command=self.show_main_menu,
                            font=('Arial', 14, 'bold'), width=20, height=2,
                            bg=self.bg_secondary, fg=self.text_secondary, relief='flat',
                            bd=0, cursor='hand2')
        back_btn.pack(pady=30)
        self.add_hover_effect(back_btn, self.text_secondary)

    def start_game(self, num_mines, difficulty_mode):
        self.difficulty_mode = difficulty_mode
        self.game = Minesweeper(10, 10, num_mines)
        self.show_game_board()

    def show_game_board(self):
        self.clear_window()
        
        # Top frame for info and timer
        top_frame = tk.Frame(self.root, bg=self.bg_card, height=90)
        top_frame.pack(fill='x', padx=15, pady=15)
        
        info_container = tk.Frame(top_frame, bg=self.bg_card)
        info_container.pack(pady=15)
        
        # Player info
        player_frame = tk.Frame(info_container, bg=self.bg_secondary, relief='flat')
        player_frame.pack(side='left', padx=10, ipadx=15, ipady=8)
        tk.Label(player_frame, text=f"👤 {self.player_name}", font=('Arial', 12, 'bold'),
                bg=self.bg_secondary, fg=self.text_primary).pack()
        
        # Difficulty info
        diff_colors = {'Easy': self.accent_green, 'Medium': '#ffa500', 'Hard': '#ff3e6c'}
        diff_frame = tk.Frame(info_container, bg=self.bg_secondary, relief='flat')
        diff_frame.pack(side='left', padx=10, ipadx=15, ipady=8)
        tk.Label(diff_frame, text=f"⚙️ {self.difficulty_mode}", font=('Arial', 12, 'bold'),
                bg=self.bg_secondary, fg=diff_colors.get(self.difficulty_mode, self.text_primary)).pack()
        
        # Timer
        timer_frame = tk.Frame(info_container, bg=self.bg_secondary, relief='flat')
        timer_frame.pack(side='left', padx=10, ipadx=15, ipady=8)
        self.timer_label = tk.Label(timer_frame, text="⏱️ 0.00s", font=('Arial', 12, 'bold'),
                                    bg=self.bg_secondary, fg=self.accent_blue)
        self.timer_label.pack()
        
        # Instructions
        info_frame = tk.Frame(self.root, bg=self.bg_primary)
        info_frame.pack(pady=8)
        tk.Label(info_frame, text="🖱️ Left Click: Reveal  |  Right Click: Flag", 
                font=('Arial', 11), bg=self.bg_primary, fg=self.text_secondary).pack()
        
        # Game board frame
        board_container = tk.Frame(self.root, bg=self.bg_card, relief='flat')
        board_container.pack(pady=15, padx=15)
        
        board_frame = tk.Frame(board_container, bg=self.bg_secondary)
        board_frame.pack(padx=15, pady=15)
        
        self.buttons = []
        for i in range(10):
            row = []
            for j in range(10):
                btn = tk.Button(board_frame, text='', width=4, height=2, 
                               font=('Arial', 11, 'bold'), bg=self.bg_card,
                               fg=self.text_primary, relief='flat', bd=0, cursor='hand2',
                               activebackground=self.bg_secondary)
                btn.grid(row=i, column=j, padx=2, pady=2)
                btn.bind('<Button-1>', lambda e, r=i, c=j: self.on_left_click(r, c))
                btn.bind('<Button-3>', lambda e, r=i, c=j: self.on_right_click(r, c))
                row.append(btn)
            self.buttons.append(row)
        
        # Bottom buttons
        bottom_frame = tk.Frame(self.root, bg=self.bg_primary)
        bottom_frame.pack(pady=15)
        
        new_game_btn = tk.Button(bottom_frame, text="🔄 New Game", command=self.show_difficulty_menu,
                                font=('Arial', 12, 'bold'), bg=self.bg_secondary,
                                fg=self.accent_blue, width=13, height=2, relief='flat',
                                bd=0, cursor='hand2')
        new_game_btn.pack(side='left', padx=8)
        self.add_hover_effect(new_game_btn, self.accent_blue)
        
        menu_btn = tk.Button(bottom_frame, text="🏠 Main Menu", command=self.show_main_menu,
                            font=('Arial', 12, 'bold'), bg=self.bg_secondary,
                            fg=self.text_secondary, width=13, height=2, relief='flat',
                            bd=0, cursor='hand2')
        menu_btn.pack(side='left', padx=8)
        self.add_hover_effect(menu_btn, self.text_secondary)
        
        self.timer_running = True
        self.update_timer()

    def update_timer(self):
        if self.timer_running and self.game:
            elapsed = self.game.get_elapsed_time()
            self.timer_label.config(text=f"⏱️ {elapsed:.2f}s")
            self.root.after(100, self.update_timer)

    def on_left_click(self, row, col):
        if not self.game:
            return
        
        result = self.game.reveal_cell(row, col)
        
        if result is None:
            return
        
        if not result:
            # Hit a mine
            self.timer_running = False
            self.reveal_all_mines()
            elapsed_time = self.game.get_elapsed_time()
            messagebox.showinfo("Game Over", f"💣 You hit a mine!\n\nTime: {elapsed_time:.2f}s")
            self.show_difficulty_menu()
        else:
            self.update_board()
            if self.game.check_win():
                self.timer_running = False
                elapsed_time = self.game.get_elapsed_time()
                play_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.game.update_leaderboard(self.player_name, elapsed_time, True, 
                                            self.difficulty_mode, play_date)
                self.reveal_all_mines()
                messagebox.showinfo("Victory!", f"🎉 You won!\n\nTime: {elapsed_time:.2f}s")
                self.show_difficulty_menu()

    def on_right_click(self, row, col):
        if not self.game:
            return
        
        if self.game.toggle_flag(row, col):
            if self.game.flagged_cells[row][col]:
                self.buttons[row][col].config(text='🚩', bg='#ff3e6c', fg=self.text_primary)
            else:
                self.buttons[row][col].config(text='', bg=self.bg_card)

    def update_board(self):
        for i in range(10):
            for j in range(10):
                if self.game.revealed_cells[i][j]:
                    cell_value = self.game.board[i][j]
                    color = self.colors.get(cell_value, self.text_primary)
                    self.buttons[i][j].config(text=cell_value, bg=self.bg_secondary, 
                                             fg=color, relief='sunken', state='disabled')

    def reveal_all_mines(self):
        for i in range(10):
            for j in range(10):
                if (i * 10 + j) in self.game.mine_locations:
                    self.buttons[i][j].config(text='💣', bg='#ff3e6c', relief='sunken')
                elif self.game.revealed_cells[i][j]:
                    cell_value = self.game.board[i][j]
                    color = self.colors.get(cell_value, self.text_primary)
                    self.buttons[i][j].config(text=cell_value, bg=self.bg_secondary, 
                                             fg=color, relief='sunken')

    def show_leaderboard(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg=self.bg_primary)
        frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Title
        title_frame = tk.Frame(frame, bg=self.bg_primary)
        title_frame.pack(pady=20)
        
        tk.Label(title_frame, text="🏆 LEADERBOARD", font=('Arial', 28, 'bold'),
                bg=self.bg_primary, fg=self.accent_blue).pack()
        tk.Label(title_frame, text="Hall of Champions", font=('Arial', 12),
                bg=self.bg_primary, fg=self.text_secondary).pack()
        
        # Create treeview container
        tree_container = tk.Frame(frame, bg=self.bg_card, relief='flat')
        tree_container.pack(expand=True, fill='both', padx=20, pady=10)
        
        tree_frame = tk.Frame(tree_container, bg=self.bg_card)
        tree_frame.pack(expand=True, fill='both', padx=15, pady=15)
        
        # Custom style for treeview
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Custom.Treeview',
                       background=self.bg_secondary,
                       foreground=self.text_primary,
                       fieldbackground=self.bg_secondary,
                       borderwidth=0,
                       relief='flat')
        style.configure('Custom.Treeview.Heading',
                       background=self.bg_card,
                       foreground=self.accent_blue,
                       borderwidth=0,
                       relief='flat',
                       font=('Arial', 11, 'bold'))
        style.map('Custom.Treeview',
                 background=[('selected', self.bg_primary)])
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        tree = ttk.Treeview(tree_frame, columns=('Rank', 'Player', 'Time', 'Difficulty', 'Date'),
                           show='headings', yscrollcommand=scrollbar.set, height=12,
                           style='Custom.Treeview')
        
        tree.heading('Rank', text='#')
        tree.heading('Player', text='Player')
        tree.heading('Time', text='Time (s)')
        tree.heading('Difficulty', text='Difficulty')
        tree.heading('Date', text='Date')
        
        tree.column('Rank', width=50, anchor='center')
        tree.column('Player', width=150)
        tree.column('Time', width=100, anchor='center')
        tree.column('Difficulty', width=100, anchor='center')
        tree.column('Date', width=180)
        
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                passwd='4589',
                database='minesweeper_leaderboard'
            )
            cursor = conn.cursor()
            cursor.execute('''SELECT player_name, elapsed_time, difficulty_mode, timestamp 
                             FROM leaderboard WHERE game_won = TRUE ORDER BY elapsed_time''')
            rows = cursor.fetchall()
            
            for idx, row in enumerate(rows, 1):
                tree.insert('', 'end', values=(f'{idx}', row[0], row[1], row[2], row[3]))
            
            cursor.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load leaderboard: {e}")
        
        scrollbar.config(command=tree.yview)
        tree.pack(expand=True, fill='both')
        
        # Back button
        back_btn = tk.Button(frame, text="← Back to Main Menu", command=self.show_main_menu,
                            font=('Arial', 14, 'bold'), width=22, height=2,
                            bg=self.bg_secondary, fg=self.text_secondary, relief='flat',
                            bd=0, cursor='hand2')
        back_btn.pack(pady=20)
        self.add_hover_effect(back_btn, self.text_secondary)

    def clear_window(self):
        self.timer_running = False
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MinesweeperGUI(root)
    root.mainloop()
