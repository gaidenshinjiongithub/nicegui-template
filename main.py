from nicegui import ui, app
import random
import zipfile
import os
from pathlib import Path
import time

# Global state
current_index = 0
running_count = 0
deck = []
card_values = {}
start_time = None
elapsed_time = 0
timer_running = False

# Serve cards directory as static files for faster loading
app.add_static_files('/cards', 'cards')

def initialize_deck():
    """Initialize the deck with card values for Hi-Lo counting"""
    global deck, card_values
    
    # Cards are already in the 'cards' folder
    cards_dir = 'cards'
    
    # DEBUG: Check if cards directory exists
    print(f"DEBUG: Cards directory exists: {os.path.exists(cards_dir)}")
    print(f"DEBUG: Current working directory: {os.getcwd()}")
    
    # List actual files in cards directory
    if os.path.exists(cards_dir):
        actual_files = os.listdir(cards_dir)
        print(f"DEBUG: Found {len(actual_files)} files in cards directory")
        print(f"DEBUG: First 5 files: {actual_files[:5]}")
    
    # Card counting values for Hi-Lo system
    # Low cards (2-6): +1
    # Mid cards (7-9): 0
    # High cards (10-A): -1
    
    suits = ['spades', 'hearts', 'diamonds', 'clubs']
    ranks = ['ace', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king']
    
    # Build deck with Hi-Lo values
    deck = []
    for suit in suits:
        for rank in ranks:
            # Your files use format: English_pattern_king_of_spades.svg
            card_filename = f"English_pattern_{rank}_of_{suit}.svg"
            # Use the static URL path instead of local file path
            card_url = f"/cards/{card_filename}"
            
            # DEBUG: Print first few card paths
            if len(deck) < 3:
                print(f"DEBUG: Card URL: {card_url}")
            
            # Assign Hi-Lo value
            if rank in ['2', '3', '4', '5', '6']:
                count_value = 1
            elif rank in ['7', '8', '9']:
                count_value = 0
            else:  # 10, J, Q, K, A
                count_value = -1
            
            deck.append({
                'name': card_filename,
                'url': card_url,
                'rank': rank,
                'suit': suit,
                'value': count_value
            })
    
    # Shuffle the deck
    random.shuffle(deck)

def hi_lo():
    """Calculate and return running count and true count"""
    global running_count, deck, current_index
    
    # For simplicity, using 1 deck
    cards_remaining = len(deck) - current_index
    decks_remaining = cards_remaining / 52.0
    
    # True count = Running count / Decks remaining
    true_count = running_count / decks_remaining if decks_remaining > 0 else 0
    
    return running_count, true_count

def update_count_display():
    """Update the count labels"""
    running, true = hi_lo()
    running_label.text = f'Running Count: {running:+d}'
    true_label.text = f'True Count: {true:+.1f}'
    
    # Color coding for advantage
    if true >= 2:
        true_label.classes('text-green-600 font-bold', remove='text-red-600 text-gray-600')
    elif true <= -2:
        true_label.classes('text-red-600 font-bold', remove='text-green-600 text-gray-600')
    else:
        true_label.classes('text-gray-600', remove='text-green-600 text-red-600')

def update_timer():
    """Update the timer display"""
    global elapsed_time, start_time, timer_running
    
    if timer_running and start_time:
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        timer_label.text = f'Time: {minutes:02d}:{seconds:02d}'

def next_card():
    """Switch to next card in deck"""
    global current_index, running_count, start_time, timer_running
    
    if current_index < len(deck):
        # Start timer on first card
        if current_index == 0:
            start_time = time.time()
            timer_running = True
            timer.activate()
        
        card = deck[current_index]
        running_count += card['value']
        current_index += 1
        
        # Update card display
        if current_index <= len(deck):
            card_label.text = f"Card {current_index} of {len(deck)}"
            
            # Display card image using static URL
            card_image.source = card['url']
            card_image.set_visibility(True)
            rank_label.set_visibility(False)
            
            # Update count display
            update_count_display()
            
            # Check if deck is finished
            if current_index >= len(deck):
                timer_running = False
                timer.deactivate()
                next_btn.disable()
                ui.notify(f'Deck Complete! Time: {int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}', type='positive')
                card_label.text = 'Deck Complete!'

def reset_game():
    """Reset the game to initial state"""
    global current_index, running_count, start_time, elapsed_time, timer_running
    
    current_index = 0
    running_count = 0
    start_time = None
    elapsed_time = 0
    timer_running = False
    timer.deactivate()
    initialize_deck()
    
    # Reset UI
    card_label.text = 'Ready to Start'
    rank_label.text = 'Click Next or press Space'
    rank_label.set_visibility(True)
    card_image.set_visibility(False)
    running_label.text = 'Running Count: 0'
    true_label.text = 'True Count: 0.0'
    timer_label.text = 'Time: 00:00'
    true_label.classes('text-gray-600', remove='text-green-600 text-red-600')
    next_btn.enable()
    
    ui.notify('Game Reset', type='info')

def main():
    """Main application setup"""
    global card_label, rank_label, running_label, true_label, next_btn, card_image, timer_label, timer
    
    # Initialize deck
    initialize_deck()
    
    # Keyboard handler for spacebar
    ui.keyboard(lambda e: next_card() if e.key == ' ' and e.action.keydown and current_index < len(deck) else None)
    
    # Page setup
    ui.colors(primary='#1976D2')
    
    with ui.column().classes('w-full items-center p-4 gap-4'):
        # Header
        ui.label('Card Counting Trainer').classes('text-3xl font-bold mb-4')
        
        # Count display and timer - Always visible at top
        with ui.card().classes('w-full max-w-md'):
            with ui.row().classes('w-full justify-around items-center'):
                running_label = ui.label('Running Count: 0').classes('text-xl font-bold')
                true_label = ui.label('True Count: 0.0').classes('text-xl font-bold text-gray-600')
            with ui.row().classes('w-full justify-center mt-2'):
                timer_label = ui.label('Time: 00:00').classes('text-2xl font-bold text-blue-600')
        
        # Timer that updates every 100ms when active
        timer = ui.timer(0.1, update_timer, active=False)
        
        # Card display area
        with ui.card().classes('w-full max-w-md min-h-64 items-center justify-center'):
            card_label = ui.label('Ready to Start').classes('text-2xl font-bold text-center')
            # Card image (hidden initially) - smaller size
            card_image = ui.image('').classes('w-48 h-auto mt-4')
            card_image.set_visibility(False)
            # Text fallback (visible initially)
            rank_label = ui.label('Click Next or press Space').classes('text-lg text-center mt-4')
        
        # Control buttons
        with ui.row().classes('gap-4'):
            next_btn = ui.button('Next Card', on_click=next_card).classes('px-8 py-3 text-lg')
            ui.button('Reset', on_click=reset_game).classes('px-8 py-3 text-lg')
        
        # Instructions
        with ui.expansion('How to Use', icon='help').classes('w-full max-w-md mt-4'):
            ui.markdown('''
            **Hi-Lo Card Counting System:**
            - Low cards (2-6): +1
            - Mid cards (7-9): 0
            - High cards (10-A): -1
            
            **Running Count:** Sum of all card values seen
            
            **True Count:** Running count divided by decks remaining
            
            **Controls:**
            - Click "Next Card" or press Space to advance
            - Green True Count (≥2): Player advantage
            - Red True Count (≤-2): House advantage
            ''')

if __name__ in {"__main__", "__mp_main__"}:
    main()
    ui.run(title='Card Counting Trainer', port=8080, reload=True)
