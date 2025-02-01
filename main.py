import pygame as pg
import sys
import threading
from settings import *
from map import *
from player import Player
from raycasting import *
from object_renderer import *
from sprite_object import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *
from network import GameServer, GameClient

class Game:
    def __init__(self) -> None:
        pg.init()
        pg.mouse.set_visible(True)
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)

        # Networking variables
        self.network_role = None  # "server" or "client"
        self.network = None
        self.server_ip = None
        self.players = {}  # Dictionary to store all players' positions and scores
        self.player_id = None

        self.main_menu()

    def main_menu(self):
        font = pg.font.Font(None, 74)
        title_text = font.render("GAME MENU", True, 'white')
        single_player_text = font.render("Single Player", True, 'white')
        multiplayer_text = font.render("Multiplayer", True, 'white')

        menu_running = True
        while menu_running:
            self.screen.fill((12, 23, 0))  # Black background
            self.screen.blit(title_text, (RES[0] // 2 - title_text.get_width() // 2, RES[1] // 4))
            self.screen.blit(single_player_text, (RES[0] // 2 - single_player_text.get_width() // 2, RES[1] // 2 - 40))
            self.screen.blit(multiplayer_text, (RES[0] // 2 - multiplayer_text.get_width() // 2, RES[1] // 2 + 40))

            pg.display.flip()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pg.mouse.get_pos()
                    if self.is_mouse_over(single_player_text, mouse_x, mouse_y):
                        self.start_single_player()
                        menu_running = False
                    # elif self.is_mouse_over(multiplayer_text, mouse_x, mouse_y): 
                    #     print(" PLAYER PLEASE WAIT")
                    #     self.choose_multiplayer_role()
                    #     menu_running = False
                    else:
                        self.is_mouse_over(multiplayer_text, mouse_x, mouse_y)
                        print("None of the menu options were selected")
                        print("Mouse position")
                        print(mouse_x, mouse_y)
                        
                        print("Single player rect")
                        print(single_player_text.get_rect())
                        
                        self.choose_multiplayer_role()
                        menu_running = False
                        
                        print("Multi player rect")
                        print(multiplayer_text.get_rect())
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:  # Escape to quit
                        pg.quit()
                        sys.exit()

    def is_mouse_over(self, text_surface, mouse_x, mouse_y):
        rect = text_surface.get_rect(center=(RES[0] // 2 - text_surface.get_width() // 2, RES[1] // 2 - 40))
        # rect = text_surface.get_rect()
        return rect.collidepoint(mouse_x, mouse_y)

    def start_single_player(self):
        print("[INFO] Starting Single Player...")
        self.network_role = "single_player"
        self.new_game()
        self.run_game()

    def choose_multiplayer_role(self):
        print("Running multiplayer")
        font = pg.font.Font(None, 74)
        title_text = font.render("Choose Role", True, 'white')
        server_text = font.render("Host a Server", True, 'white')
        client_text = font.render("Join as Client", True, 'white')

        print("[INFO] Starting Multiplayer Role Selection...")

        # Calculate text positions
        title_pos = (RES[0] // 2 - title_text.get_width() // 2, RES[1] // 4)
        server_pos = (RES[0] // 2 - server_text.get_width() // 2, RES[1] // 2 - 40)
        client_pos = (RES[0] // 2 - client_text.get_width() // 2, RES[1] // 2 + 40)

        # Create clickable areas for server and client
        server_rect = server_text.get_rect(center=(RES[0] // 2, RES[1] // 2 - 40))
        client_rect = client_text.get_rect(center=(RES[0] // 2, RES[1] // 2 + 40))

        menu_running = True
        while menu_running:
            self.screen.fill((0, 0, 0))  # Black background
            self.screen.blit(title_text, title_pos)
            self.screen.blit(server_text, server_pos)
            self.screen.blit(client_text, client_pos)

            # Update the display
            pg.display.flip()

            # Handle events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    print("[INFO] Quit event detected. Exiting...")
                    pg.quit()
                    sys.exit()

                if event.type == pg.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    print(f"[DEBUG] Mouse clicked at: {mouse_x}, {mouse_y}")

                    if server_rect.collidepoint(mouse_x, mouse_y):  # Check click on "Host a Server"
                        print("[INFO] Hosting a server...")
                        self.start_server()
                        menu_running = False
                        break
                    elif client_rect.collidepoint(mouse_x, mouse_y):  # Check click on "Join as Client"
                        print("[INFO] Joining as a client...")
                        self.start_client()
                        menu_running = False
                        break

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:  # Escape to quit
                        print("[INFO] Escape key pressed. Exiting...")
                        pg.quit()
                        sys.exit()


    def start_server(self):
        print("[INFO] Starting Server...")
        self.network_role = "server"
        self.network = GameServer()

        # Start the server in a separate thread
        threading.Thread(target=self.network.start, daemon=True).start()

        # Show "Looking for players..." message
        self.show_waiting_message()

    def start_client(self):
        print("[INFO] Starting Client...")
        self.network_role = "client"
        self.server_ip = input("Enter server IP address: ")
        self.network = GameClient(self.server_ip)

        # Start receiving messages in a separate thread
        threading.Thread(target=self.receive_messages, daemon=True).start()

        print("[INFO] Attempting to connect to server...")
        self.network.send_message("PLAYER_JOINED")

        # Start the game as soon as we connect
        self.wait_for_players()

    def show_waiting_message(self):
        font = pg.font.Font(None, 74)
        waiting_text = font.render("Looking for players...", True, 'white')
        self.screen.fill((0, 0, 0))  # Black background
        self.screen.blit(waiting_text, (RES[0] // 2 - waiting_text.get_width() // 2, RES[1] // 2))
        pg.display.flip()

        # Wait for players to connect
        while len(self.network.clients) < 2:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        pg.quit()
                        sys.exit()

        print("[INFO] Players are connected, starting the game...")
        self.new_game()
        self.run_game()

    def wait_for_players(self):
        # This method will be used for the client to wait for the server to start the game
        font = pg.font.Font(None, 74)
        waiting_text = font.render("Waiting for players...", True, 'white')
        self.screen.fill((0, 0, 0))  # Black background
        self.screen.blit(waiting_text, (RES[0] // 2 - waiting_text.get_width() // 2, RES[1] // 2))
        pg.display.flip()

        # Wait for the server to start the game
        while not self.network.is_game_started:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        pg.quit()
                        sys.exit()

        self.new_game()
        self.run_game()

    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)  # Correctly initialize the player with 'self' only
        self.players[self.player_id] = (self.player.x, self.player.y)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)

    def update(self):
        self.player.update()

        # Sync player actions via the network
        if self.network_role == "server":
            self.network.broadcast(f"PLAYER_MOVED:{self.player_id},{self.player.x},{self.player.y}")
        elif self.network_role == "client":
            self.network.send_message(f"PLAYER_MOVED:{self.player_id},{self.player.x},{self.player.y}")

        # Process incoming messages
        if self.network:
            while self.network.messages:
                message = self.network.messages.pop(0)
                self.process_network_message(message)

        self.raycasting.update()
        self.object_handler.update()
        self.weapon.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() : .1f}')

    def process_network_message(self, message):
        if message.startswith("PLAYER_MOVED:"):
            _, player_id, x, y = message.split(",")
            self.players[int(player_id)] = (float(x), float(y))
            print(f"[NETWORK] Player {player_id} moved to ({x}, {y})")
        elif message == "PLAYER_SHOT":
            print("[NETWORK] Another player shot!")

    def draw(self):
        self.object_renderer.draw()
        self.weapon.draw()

        # Draw other players
        for player_id, (x, y) in self.players.items():
            pg.draw.circle(self.screen, 'red', (int(x), int(y)), 10)

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            self.player.single_fire_event(event)

            # Send shooting event to the server
            if self.network_role == "client" and event.type == pg.MOUSEBUTTONDOWN:
                self.network.send_message("PLAYER_SHOT")

    def run_game(self):
        while True:
            self.check_events()
            self.update()
            self.draw()

    def receive_messages(self):
        while True:
            if self.network_role == "client":
                message = self.network.receive_messages()
                if message:
                    self.process_network_message(message)

if __name__ == '__main__':
    game = Game()  
    game.run_game()
