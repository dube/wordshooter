import arcade
import random
import time

SCREEN_WIDTH=1000
SCREEN_HEIGHT=800
SCREEN_TITLE="Word Blaster"

CHARACTER_SCALING=1
PLAYER_MOVEMENT_SPEED=8
BULLET_SPEED=15

SPEECH_RECOGNITION=True
PLAY_MUSIC=False

if SPEECH_RECOGNITION:
    import speech_recognition as sr
    import _thread
    import pyaudio

# difficulty
WORD_SPEED=1
WORDS_ON_SCREEN=3

class Ship(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.scale=CHARACTER_SCALING
        self.center_x = 60
        self.center_y = 60

        self.shield = 5

        self.animate_damage = 0
        self.store_x = self.center_x
        self.store_y = self.center_y
        
        main_path="assets/PNG/"
        self.texture = arcade.load_texture(f"{main_path}playerShip1_blue.png")
        self.damagesound = arcade.Sound("assets/Bonus/sfx_shieldDown.ogg")
    def update(self):
        super().update()

        if self.center_x >= SCREEN_WIDTH-40:
            self.center_x = SCREEN_WIDTH-40
        elif self.center_x <= 50:
            self.center_x = 50

        if self.animate_damage == 0:
            self.store_x = self.center_x
            self.store_y = self.center_y

        if self.animate_damage == 1:
            self.damagesound.play(pan=0,volume=.1)

        if self.animate_damage > 0 and self.animate_damage < 5:
            self.center_x += (self.animate_damage%2==1)*-5 + (self.animate_damage%2==0)*5
            self.center_y += (self.animate_damage%2==1)*-5 + (self.animate_damage%2==0)*5
            self.animate_damage += 1
        elif self.animate_damage >= 5:
            self.center_x=self.store_x
            self.center_y=self.store_y
            self.animate_damage = 0

class Bullet(arcade.Sprite):
    def __init__(self, center_x, center_y):
        super().__init__()

        self.scale=CHARACTER_SCALING
        self.center_x = center_x
        self.center_y = center_y+40

        main_path="assets/PNG/Lasers/"
        self.texture=arcade.load_texture(f"{main_path}laserBlue08.png")

    def update(self):
        super().update()

        # make the bullet go in the right direction
        self.change_y = BULLET_SPEED

        # get rid of this bullet if it left the screen
        if self.bottom > SCREEN_HEIGHT:
            self.remove_from_sprite_lists()

class Word:
    def __init__(self, word, x, y, speed):
        self.word = word
        self.typed_word = None 
        self.x = x
        self.y = y
        self.speed = speed
        self.attack_pos = 0
        self.destroy=0
        self.animate_destroy=0
        self.bullet = None

    def draw(self):
        arcade.draw_text(self.word, self.x, self.y,
                arcade.color.WHITE, 24)
        if self.typed_word != None:
            arcade.draw_text(self.typed_word, self.x, self.y,
                    arcade.color.ORANGE, 24)

    def attack_letter(self, key):
        if self.destroy==0:
            if self.word[self.attack_pos].lower() == chr(key):
                self.attack_pos += 1
                if len(self.word) == self.attack_pos:
                    self.typed_word=self.word
                    self.destroy=1
                    self.animate_destroy=1
                    return 1
                else:
                    self.typed_word=self.word[0:self.attack_pos] 
                    return 0

        return 0

    def attack_word(self, word):
        # some fixes for incorrect recognition choices:
        word = word.lower()
        if word == "4":
            word = "for"
        elif word == "2":
            word = "to"
        elif word == "ar":
            word = "are"
        elif word == "b":
            word = "be"
        elif word == "orr":
            word = "or"

        if self.destroy==0:
            if self.word.lower() == word:
                self.typed_word=self.word
                self.destroy=1
                self.animate_destroy=1
                return 1
            else:
                return 0
        return 0



class Star:
    def __init__(self, screen_width, screen_height):
        self.x = random.randrange(screen_width + 200)
        self.y = random.randrange(screen_height)
        self.size = random.randrange(4)
        self.speed = random.randrange(20, 40)
        self.color = random.choice([arcade.color.PURPLE, arcade.color.BLUEBERRY])
    
    def draw(self):
        arcade.draw_circle_filled(self.x, self.y, self.size, self.color)
    
    def reset_pos(self, screen_width, screen_height):
        self.x = random.randint(0, screen_width + 100)
        self.y = screen_height



class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.player_list=None
        self.bullet_list=None
        self.word_list=None
        self.star_list=None
        self.spokenwords=None

        self.score=0

        self.word_count=0
        self.word_create_delay=0

        self.words = ["what","this","his","I","or","her"
                ,"word","that","the","poop","can","at"
                ,"dog","from","frog","have","it","is"
                ,"in","for","but","Sonic","Shadow","was"
                ,"on","we","are","be","with","you"
                ,"your","and","me","my","as","he"
                ,"to","of","if"]

        arcade.set_background_color(arcade.csscolor.BLACK)

        self.lasersound = arcade.Sound("assets/Bonus/sfx_laser2.ogg")
        if PLAY_MUSIC:
            self.music = arcade.Sound("assets/Bonus/solar_striker1.mp3",streaming=True)

    def setup(self,spokenwords):
        self.player_list=arcade.SpriteList()
        self.bullet_list=arcade.SpriteList()
        self.word_list=set()
        self.star_list=set()

        self.spokenwords = spokenwords
        
        self.player_sprite=Ship()

        self.player_list.append(self.player_sprite)

        self.create_word()
        
        if PLAY_MUSIC:
            self.music.play(pan=0,volume=.01)

        for _ in range(30):
            self.create_star()


    def on_draw(self):
        arcade.start_render()

        self.player_list.draw()
        self.bullet_list.draw()

        for word in self.word_list:
            word.draw()

        for star in self.star_list:
            star.draw()

        score_text = f"Score: {self.score} Shield: {self.player_sprite.shield}"
        arcade.draw_text(score_text, 10, 10,
                arcade.csscolor.WHITE, 18)

    def update(self, delta_time):

        # use speech recognition to attack the words
        if SPEECH_RECOGNITION:
            if self.spokenwords.newwords == 1:
                for request in self.spokenwords.wordlist.split():
                    for word in self.word_list:
                        hit=word.attack_word(request)
                        if hit > 0:
                            self.score += 1
                self.spokenwords.newwords=0
                self.spokenwords.wordlist=""


        if PLAY_MUSIC:
            if self.music.get_stream_position() == 0.0:
                self.music.play(pan=0,volume=.01)
                time.sleep(0.03)

        for star in self.star_list:
            star.y -= star.speed
            if star.y < 0:
                star.reset_pos(SCREEN_WIDTH,SCREEN_HEIGHT)

        self.word_create_delay += 1

        for word in self.word_list:
            word.y -= word.speed
            
            if word.y < 0:
                word.destroy=1
                word.animate_destroy=0
                self.player_sprite.animate_damage = 1
                self.player_sprite.shield -= 1

            if word.animate_destroy==1:

                if word.x < self.player_sprite.center_x:
                    if word.bullet is None:
                        self.player_sprite.change_x=-PLAYER_MOVEMENT_SPEED
                elif word.x-5 > self.player_sprite.center_x:
                    if word.bullet is None:
                        self.player_sprite.change_x=PLAYER_MOVEMENT_SPEED
                
                if word.bullet is None:
                    if self.player_sprite.center_x >= word.x-5 and self.player_sprite.center_x <= word.x+5:
                        word.bullet=self.create_bullet()
                elif word.bullet is not None:
                    if word.bullet.center_y >= word.y:
                        word.animate_destroy=0
                        word.bullet.remove_from_sprite_lists()


            if word.destroy==1 and word.animate_destroy==0:
                self.word_list.discard(word)
                self.create_word()

        if self.word_count < WORDS_ON_SCREEN-1 and self.word_create_delay > 80:
            self.create_word()
            self.word_count += 1
            self.word_create_delay = 0

        self.player_list.update()
        self.bullet_list.update()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.close_window()

        for word in self.word_list:
            hit = word.attack_letter(key) 
            if hit > 0:
                self.score += 1

                

    def create_bullet(self):
        bullet = Bullet(self.player_sprite.center_x,self.player_sprite.center_y)
        self.bullet_list.append(bullet)
        self.lasersound.play(pan=0,volume=.1)
        return bullet

    def create_word(self):
        rand_word = random.choice(self.words)
        speed = WORD_SPEED * (1/random.randint(1,3))

        self.word_list.add(Word(rand_word, random.randint(50,SCREEN_WIDTH-80), SCREEN_HEIGHT, speed))

    def create_star(self):
        self.star_list.add(Star(SCREEN_WIDTH,SCREEN_HEIGHT))

# this function runs in a separate thread to listen for words
def live_speech(threadname,spokenwords,recognizer,microphone):
    with microphone as source:
        while True:
            try:
                #recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, phrase_time_limit=2)
                text = recognizer.recognize_google(audio, language="en-US")

                print(f"heard: {text}")
                
                spokenwords.wordlist += " "
                spokenwords.wordlist += text
                spokenwords.newwords = 1


            except:
                print("Couldn't understand audio")
                
class SpokenWord:
    def __init__(self):
        self.wordlist=""
        self.newwords=0

    

def main():

    # object that is used to communicate between threads
    spokenwords = SpokenWord()

    if SPEECH_RECOGNITION:
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        # set up the speech recognition thread
        try:
            _thread.start_new_thread(live_speech, ("Speech Thread", spokenwords,recognizer,microphone,))
        except:
            print("Error opening speech thread")

    window=GameWindow()
    window.setup(spokenwords)
    arcade.run()


if __name__ == "__main__":
    main()
