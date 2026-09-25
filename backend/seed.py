"""
Seed script — run once to create quiz.db.
10 easy + 10 medium + 10 hard per category = 30 per category = 180 total questions.
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import init_db, get_connection, DB_PATH

CATEGORIES = [
    {"key": "general",   "name": "General Knowledge", "icon": "🧠"},
    {"key": "movies",    "name": "Movies & TV",       "icon": "🎬"},
    {"key": "science",   "name": "Science",           "icon": "🔬"},
    {"key": "history",   "name": "History",           "icon": "🏛️"},
    {"key": "geography", "name": "Geography",         "icon": "🌍"},
    {"key": "sports",    "name": "Sports",            "icon": "⚽"},
]

# fmt: off
# (question, [opt0,opt1,opt2,opt3], correct_index, difficulty)
QUESTIONS = {
    "general": [
        # ── EASY (10) ──────────────────────────────────────────────────────
        ("What is the largest organ in the human body?",                    ["Liver","Skin","Heart","Lungs"],                          1, "easy"),
        ("How many continents are there on Earth?",                         ["5","6","7","8"],                                         2, "easy"),
        ("What is the smallest prime number?",                              ["0","1","2","3"],                                         2, "easy"),
        ("What do you call a group of lions?",                              ["Pack","Pride","Herd","Colony"],                          1, "easy"),
        ("Which planet is known as the Red Planet?",                        ["Venus","Jupiter","Mars","Saturn"],                       2, "easy"),
        ("What is the capital of Australia?",                               ["Sydney","Melbourne","Canberra","Perth"],                 2, "easy"),
        ("How many days are there in a leap year?",                         ["364","365","366","367"],                                 2, "easy"),
        ("How many sides does a hexagon have?",                             ["4","5","6","7"],                                         2, "easy"),
        ("What is the capital of France?",                                  ["Berlin","Madrid","Paris","Rome"],                        2, "easy"),
        ("What color is a ripe banana?",                                    ["Green","Orange","Yellow","Red"],                         2, "easy"),
        # ── MEDIUM (10) ────────────────────────────────────────────────────
        ("Which language has the most native speakers worldwide?",          ["English","Hindi","Mandarin Chinese","Spanish"],          2, "medium"),
        ("How many strings does a standard violin have?",                   ["4","5","6","8"],                                         0, "medium"),
        ("What is the chemical symbol for gold?",                           ["Go","Gd","Au","Ag"],                                     2, "medium"),
        ("How many bones are in the adult human body?",                     ["186","206","226","246"],                                 1, "medium"),
        ("What is the hardest natural substance on Earth?",                 ["Titanium","Diamond","Quartz","Sapphire"],                1, "medium"),
        ("Which blood type is known as the universal donor?",               ["A+","B−","O−","AB+"],                                   2, "medium"),
        ("What is the largest ocean on Earth?",                             ["Atlantic","Indian","Arctic","Pacific"],                  3, "medium"),
        ("In which year did humans first land on the Moon?",                ["1965","1967","1969","1971"],                             2, "medium"),
        ("Which planet has the most moons in our solar system?",            ["Jupiter","Uranus","Neptune","Saturn"],                   3, "medium"),
        ("What is the square root of 169?",                                 ["11","12","13","14"],                                     2, "medium"),
        # ── HARD (10) ──────────────────────────────────────────────────────
        ("What is the rarest blood type in humans?",                        ["O−","B−","AB−","A+"],                                   2, "hard"),
        ("In what year was the United Nations founded?",                    ["1942","1945","1948","1950"],                             1, "hard"),
        ("What is the only letter that does not appear in any US state name?", ["Q","X","Z","Y"],                                    0, "hard"),
        ("Which element has the highest melting point?",                    ["Tungsten","Iron","Titanium","Platinum"],                 0, "hard"),
        ("How many time zones does the world have in total?",               ["12","18","24","36"],                                     2, "hard"),
        ("What is the shortest war in recorded history (Anglo-Zanzibar)?",  ["38 minutes","2 hours","45 minutes","1 hour"],           0, "hard"),
        ("What is Avogadro's number (approximate)?",                        ["3.14×10²³","6.02×10²³","1.38×10²³","9.81×10²³"],       1, "hard"),
        ("Which element was named after Marie Curie's home country?",       ["Radium","Polonium","Curium","Thorium"],                  1, "hard"),
        ("In what year did Mendeleev first publish the periodic table?",    ["1849","1869","1889","1909"],                             1, "hard"),
        ("What is the basic physical and functional unit of heredity?",     ["Chromosome","Allele","Gene","Nucleotide"],               2, "hard"),
    ],

    "movies": [
        # ── EASY (10) ──────────────────────────────────────────────────────
        ("Which studio produces the 'Toy Story' franchise?",               ["DreamWorks","Pixar","Illumination","Blue Sky"],          1, "easy"),
        ("What color is Kermit the Frog?",                                  ["Blue","Yellow","Green","Purple"],                        2, "easy"),
        ("What type of creature is Shrek?",                                 ["Troll","Ogre","Goblin","Giant"],                         1, "easy"),
        ("In which decade was the first 'Star Wars' film released?",        ["1960s","1970s","1980s","1990s"],                         1, "easy"),
        ("What is the name of the coffee shop in 'Friends'?",               ["Central Perk","The Grind","Java Joe's","Perk Place"],   0, "easy"),
        ("Which actor played the lead in 'The Matrix'?",                    ["Brad Pitt","Tom Cruise","Keanu Reeves","Will Smith"],    2, "easy"),
        ("Which streaming platform released 'The Crown'?",                  ["Hulu","Netflix","Amazon Prime","Disney+"],               1, "easy"),
        ("In 'The Lion King', what is Simba's father's name?",              ["Mufasa","Scar","Rafiki","Timon"],                        0, "easy"),
        ("Which film features a clownfish looking for his son?",            ["Shrek","Ice Age","Finding Nemo","Moana"],                2, "easy"),
        ("In 'Toy Story', what does Buzz Lightyear say his catchphrase is?",["To infinity and beyond!","I'll be back","Hakuna Matata","You've got a friend in me"], 0, "easy"),
        # ── MEDIUM (10) ────────────────────────────────────────────────────
        ("Who directed 'Jaws' and 'E.T.'?",                                ["George Lucas","Steven Spielberg","Martin Scorsese","James Cameron"], 1, "medium"),
        ("Which show is set in the fictional town of Hawkins?",             ["Riverdale","Stranger Things","Twin Peaks","Wednesday"],  1, "medium"),
        ("Who composed the score for 'Jurassic Park'?",                    ["Hans Zimmer","John Williams","Danny Elfman","Alan Silvestri"], 1, "medium"),
        ("What was the first feature-length animated movie ever released?", ["Snow White and the Seven Dwarfs","Pinocchio","Fantasia","Bambi"], 0, "medium"),
        ("Which film won the first Academy Award for Best Picture?",        ["Wings","Sunrise","The Jazz Singer","Metropolis"],        0, "medium"),
        ("In 'The Godfather', what is the family's surname?",               ["Corleone","Soprano","Barzini","Tattaglia"],              0, "medium"),
        ("Which 1994 film features the quote 'Life is like a box of chocolates'?",["The Shawshank Redemption","Forrest Gump","Pulp Fiction","The Lion King"], 1, "medium"),
        ("Which actor plays Tony Stark/Iron Man in the MCU?",              ["Chris Hemsworth","Robert Downey Jr.","Mark Ruffalo","Chris Evans"], 1, "medium"),
        ("In which year was the first Harry Potter film released?",         ["1999","2000","2001","2002"],                             2, "medium"),
        ("What is the fictional African country in 'Black Panther'?",       ["Zamunda","Wakanda","Genosha","Latveria"],                1, "medium"),
        # ── HARD (10) ──────────────────────────────────────────────────────
        ("What is the name of the fictional metal in Captain America's shield?",["Adamantium","Vibranium","Uru","Carbonadium"],       1, "hard"),
        ("Which filmmaker directed 'Mulholland Drive' and 'Blue Velvet'?",  ["David Cronenberg","David Fincher","David Lynch","David Lean"], 2, "hard"),
        ("In 'Blade Runner', what year is the story set?",                  ["2017","2019","2021","2025"],                             1, "hard"),
        ("Which Alfred Hitchcock film features the Bates Motel?",           ["Vertigo","Psycho","Rear Window","The Birds"],            1, "hard"),
        ("What was Stanley Kubrick's last completed film?",                  ["Full Metal Jacket","A.I.","Eyes Wide Shut","The Shining"], 2, "hard"),
        ("In 'Inception', how many levels of dreams does the team plan to go?",["2","3","4","5"],                                     1, "hard"),
        ("Who directed '2001: A Space Odyssey'?",                           ["Ridley Scott","Steven Spielberg","Stanley Kubrick","David Lynch"], 2, "hard"),
        ("Which film won the Academy Award for Best Picture in 2020?",      ["1917","Joker","Parasite","Ford v Ferrari"],              2, "hard"),
        ("What does Andy Dufresne use to escape in 'The Shawshank Redemption'?",["A tunnel","A spoon","A rock hammer","A key"],      2, "hard"),
        ("What is the name of the ship in 'Alien' (1979)?",                 ["Sulaco","Discovery One","Nostromo","Prometheus"],        2, "hard"),
    ],

    "science": [
        # ── EASY (10) ──────────────────────────────────────────────────────
        ("What gas do plants absorb from the atmosphere for photosynthesis?",["Oxygen","Nitrogen","Carbon dioxide","Hydrogen"],        2, "easy"),
        ("What is H2O more commonly known as?",                            ["Salt","Hydrogen peroxide","Water","Sugar"],              2, "easy"),
        ("What part of the plant conducts photosynthesis?",                ["Root","Stem","Leaf","Flower"],                           2, "easy"),
        ("What is the powerhouse of the cell?",                            ["Nucleus","Ribosome","Mitochondria","Golgi body"],        2, "easy"),
        ("What force keeps planets in orbit around the sun?",              ["Magnetism","Gravity","Friction","Inertia"],              1, "easy"),
        ("How many chambers does the human heart have?",                   ["2","3","4","5"],                                         2, "easy"),
        ("What type of animal is a Komodo dragon?",                        ["Snake","Lizard","Crocodile","Amphibian"],                1, "easy"),
        ("Which planet is closest to the Sun?",                            ["Venus","Earth","Mercury","Mars"],                        2, "easy"),
        ("What is the boiling point of water in Celsius?",                 ["90°C","95°C","100°C","110°C"],                          2, "easy"),
        ("What do bees produce?",                                          ["Silk","Wax","Honey","Venom"],                            2, "easy"),
        # ── MEDIUM (10) ────────────────────────────────────────────────────
        ("What is the speed of light approximately?",                      ["300,000 km/s","150,000 km/s","1,000,000 km/s","30,000 km/s"], 0, "medium"),
        ("Which element has the atomic number 1?",                         ["Helium","Hydrogen","Oxygen","Carbon"],                   1, "medium"),
        ("What is the study of earthquakes called?",                       ["Geology","Meteorology","Seismology","Volcanology"],      2, "medium"),
        ("What is the most abundant gas in Earth's atmosphere?",           ["Oxygen","Carbon dioxide","Nitrogen","Argon"],            2, "medium"),
        ("What is the chemical formula for table salt?",                   ["NaOH","NaCl","KCl","HCl"],                              1, "medium"),
        ("What organelle is responsible for producing proteins?",           ["Mitochondria","Ribosome","Lysosome","Nucleus"],          1, "medium"),
        ("What is the SI unit of electric current?",                       ["Volt","Watt","Ampere","Ohm"],                            2, "medium"),
        ("How many bones are in the human skull?",                         ["12","22","32","42"],                                     1, "medium"),
        ("What is the most abundant metal in Earth's crust?",              ["Iron","Copper","Aluminium","Silicon"],                   2, "medium"),
        ("Newton's First Law of Motion is also known as the Law of…?",    ["Acceleration","Inertia","Gravity","Action"],             1, "medium"),
        # ── HARD (10) ──────────────────────────────────────────────────────
        ("What is the Chandrasekhar limit in solar masses?",               ["0.5","1.0","1.4","2.0"],                                 2, "hard"),
        ("What is the half-life of Carbon-14 (approximately)?",            ["1,200 years","5,730 years","10,500 years","25,000 years"], 1, "hard"),
        ("What is the name of the particle that carries the strong nuclear force?",["Photon","Gluon","W Boson","Graviton"],         1, "hard"),
        ("The Heisenberg Uncertainty Principle is about the limits of knowing what simultaneously?",["Mass and charge","Position and momentum","Speed and acceleration","Energy and time"], 1, "hard"),
        ("What is the pH of pure water at 25°C?",                          ["6.0","7.0","7.4","8.0"],                                 1, "hard"),
        ("Which law states that entropy of an isolated system always increases?",["First law of thermodynamics","Second law of thermodynamics","Third law of thermodynamics","Zeroth law of thermodynamics"], 1, "hard"),
        ("What is the theoretical boundary around a black hole from which nothing can escape?",["Photon sphere","Schwarzschild radius","Event horizon","Singularity"], 2, "hard"),
        ("Which subatomic particle was discovered by James Chadwick in 1932?",["Proton","Electron","Neutron","Positron"],             2, "hard"),
        ("The atomic mass of Carbon-12 is exactly how many atomic mass units?",["10","11","12","14"],                                 2, "hard"),
        ("Which law states that pressure and volume of a gas are inversely proportional at constant temperature?",["Charles's Law","Avogadro's Law","Boyle's Law","Dalton's Law"], 2, "hard"),
    ],

    "history": [
        # ── EASY (10) ──────────────────────────────────────────────────────
        ("In which year did World War II end?",                            ["1943","1945","1947","1950"],                             1, "easy"),
        ("Who was the first President of the United States?",             ["Thomas Jefferson","John Adams","George Washington","James Madison"], 2, "easy"),
        ("Which ancient civilization built the pyramids of Giza?",        ["Romans","Greeks","Egyptians","Mesopotamians"],           2, "easy"),
        ("The Great Wall is located in which country?",                   ["Japan","China","Mongolia","South Korea"],                1, "easy"),
        ("What year did the Titanic sink?",                               ["1905","1912","1918","1923"],                             1, "easy"),
        ("Which wall divided a European city until 1989?",                ["Vienna Wall","Berlin Wall","Warsaw Wall","Prague Wall"], 1, "easy"),
        ("The Renaissance began in which country?",                       ["France","Spain","Italy","Germany"],                      2, "easy"),
        ("Who painted the Mona Lisa?",                                    ["Michelangelo","Leonardo da Vinci","Raphael","Rembrandt"], 1, "easy"),
        ("Columbus represented which country when he reached America?",   ["Portugal","England","Spain","France"],                   2, "easy"),
        ("Who was the first man to walk on the Moon?",                    ["Buzz Aldrin","Neil Armstrong","Yuri Gagarin","Alan Shepard"], 1, "easy"),
        # ── MEDIUM (10) ────────────────────────────────────────────────────
        ("Which empire was ruled by Julius Caesar?",                      ["Ottoman Empire","Roman Empire","Persian Empire","British Empire"], 1, "medium"),
        ("Who wrote the Declaration of Independence?",                    ["Benjamin Franklin","Thomas Jefferson","Alexander Hamilton","John Hancock"], 1, "medium"),
        ("Who was known as the 'Maid of Orléans'?",                       ["Marie Antoinette","Joan of Arc","Catherine the Great","Eleanor of Aquitaine"], 1, "medium"),
        ("What treaty ended World War I?",                                ["Treaty of Paris","Treaty of Versailles","Treaty of Vienna","Treaty of Ghent"], 1, "medium"),
        ("Which explorer is credited with discovering America in 1492?",  ["Vasco da Gama","Ferdinand Magellan","Christopher Columbus","Amerigo Vespucci"], 2, "medium"),
        ("In what year did the French Revolution begin?",                 ["1776","1783","1789","1799"],                             2, "medium"),
        ("In which year was the Magna Carta signed?",                     ["1066","1215","1415","1600"],                             1, "medium"),
        ("Which was Napoleon's greatest military victory?",               ["Waterloo","Austerlitz","Leipzig","Borodino"],            1, "medium"),
        ("Who was the first emperor of China?",                           ["Kublai Khan","Sun Yat-sen","Qin Shi Huang","Liu Bang"],  2, "medium"),
        ("The Battle of Waterloo was fought in which country?",           ["France","Belgium","Germany","Netherlands"],              1, "medium"),
        # ── HARD (10) ──────────────────────────────────────────────────────
        ("What was the code name for the Allied invasion of Normandy?",   ["Operation Barbarossa","Operation Overlord","Operation Market Garden","Operation Torch"], 1, "hard"),
        ("Which battle is considered the turning point of the American Civil War?",["Antietam","Gettysburg","Bull Run","Shiloh"],   1, "hard"),
        ("In what year did the Byzantine Empire fall to the Ottomans?",   ["1389","1453","1492","1517"],                             1, "hard"),
        ("Which civilization invented the concept of zero as a number?",  ["Greek","Egyptian","Indian","Chinese"],                  2, "hard"),
        ("Who was the last pharaoh of ancient Egypt?",                    ["Nefertiti","Cleopatra VII","Hatshepsut","Ramesses II"],  1, "hard"),
        ("In what year did the Ottoman Empire formally end?",             ["1918","1920","1922","1924"],                             2, "hard"),
        ("Which treaty ended the Thirty Years' War?",                     ["Treaty of Westphalia","Treaty of Utrecht","Peace of Augsburg","Treaty of Paris"], 0, "hard"),
        ("Who was the last Tsar of Russia?",                              ["Alexander III","Nicholas I","Nicholas II","Alexander II"], 2, "hard"),
        ("The Peloponnesian War was fought primarily between which two city-states?",["Athens and Sparta","Rome and Carthage","Corinth and Thebes","Macedon and Persia"], 0, "hard"),
        ("Which US president signed the Emancipation Proclamation?",      ["Ulysses Grant","Abraham Lincoln","Andrew Johnson","James Buchanan"], 1, "hard"),
    ],

    "geography": [
        # ── EASY (10) ──────────────────────────────────────────────────────
        ("What is the longest river in the world?",                       ["Amazon","Nile","Yangtze","Mississippi"],                 1, "easy"),
        ("What is the smallest country in the world?",                    ["Monaco","San Marino","Vatican City","Liechtenstein"],    2, "easy"),
        ("What is the capital of Canada?",                                ["Toronto","Vancouver","Ottawa","Montreal"],               2, "easy"),
        ("Which ocean is the largest by surface area?",                   ["Atlantic","Indian","Arctic","Pacific"],                  3, "easy"),
        ("What is the driest inhabited continent?",                       ["Africa","Australia","Antarctica","Asia"],               1, "easy"),
        ("What is the tallest mountain on Earth?",                        ["K2","Kangchenjunga","Mount Everest","Lhotse"],           2, "easy"),
        ("What is the capital of Japan?",                                 ["Seoul","Beijing","Tokyo","Bangkok"],                     2, "easy"),
        ("On which continent is Egypt located?",                          ["Asia","South America","Europe","Africa"],               3, "easy"),
        ("What is the largest continent by area?",                        ["Africa","North America","Asia","Europe"],               2, "easy"),
        ("What is the capital of Brazil?",                                ["Rio de Janeiro","São Paulo","Brasília","Salvador"],      2, "easy"),
        # ── MEDIUM (10) ────────────────────────────────────────────────────
        ("Which country has the largest population?",                     ["United States","India","China","Indonesia"],            1, "medium"),
        ("Mount Everest is on the border of which two countries?",        ["India & China","Nepal & China","Nepal & India","Bhutan & China"], 1, "medium"),
        ("Which desert is the largest in the world?",                     ["Sahara","Gobi","Antarctic","Kalahari"],                  2, "medium"),
        ("How many time zones does Russia span?",                         ["7","9","11","13"],                                       2, "medium"),
        ("Which African country is entirely surrounded by South Africa?", ["Botswana","Eswatini","Lesotho","Zimbabwe"],             2, "medium"),
        ("What is the deepest point in the ocean?",                       ["Tonga Trench","Mariana Trench","Java Trench","Puerto Rico Trench"], 1, "medium"),
        ("Which country has the most of the Amazon rainforest?",          ["Peru","Colombia","Brazil","Venezuela"],                  2, "medium"),
        ("What is the longest mountain range in the world?",              ["Himalayas","Rocky Mountains","Andes","Alps"],            2, "medium"),
        ("Which sea separates Italy from the Balkans?",                   ["Tyrrhenian Sea","Adriatic Sea","Ionian Sea","Aegean Sea"], 1, "medium"),
        ("Which country is in both Europe and Asia?",                     ["Egypt","Turkey","Morocco","Tunisia"],                    1, "medium"),
        # ── HARD (10) ──────────────────────────────────────────────────────
        ("What is the only country to span four hemispheres?",            ["Brazil","Indonesia","Kiribati","Russia"],               2, "hard"),
        ("Which lake is the deepest in the world?",                       ["Lake Superior","Lake Baikal","Lake Tanganyika","Caspian Sea"], 1, "hard"),
        ("Which strait separates Africa from Europe?",                    ["Strait of Hormuz","Strait of Malacca","Strait of Gibraltar","Bosphorus"], 2, "hard"),
        ("What is the largest island in the world (not counting continents)?",["Borneo","Madagascar","Greenland","New Guinea"],     2, "hard"),
        ("Which river flows through the most capital cities?",            ["Rhine","Danube","Mekong","Nile"],                        1, "hard"),
        ("Which country has the most UNESCO World Heritage Sites?",       ["China","France","Italy","Spain"],                        2, "hard"),
        ("What percentage of the Earth's water is freshwater?",           ["1%","3%","10%","20%"],                                   1, "hard"),
        ("What connects North and South America?",                        ["Yucatan Peninsula","Baja California","Isthmus of Panama","Gulf of Mexico"], 2, "hard"),
        ("Which African country has three capital cities?",               ["Nigeria","Ethiopia","South Africa","Kenya"],            2, "hard"),
        ("What is the most densely populated country in the world?",      ["Bangladesh","Singapore","Monaco","Malta"],              2, "hard"),
    ],

    "sports": [
        # ── EASY (10) ──────────────────────────────────────────────────────
        ("How many players are on a standard football (soccer) team on the field?",["9","10","11","12"],                            2, "easy"),
        ("In which sport would you perform a 'slam dunk'?",               ["Volleyball","Basketball","Tennis","Badminton"],         1, "easy"),
        ("How often are the Summer Olympic Games held?",                  ["Every 2 years","Every 3 years","Every 4 years","Every 5 years"], 2, "easy"),
        ("How many rings are on the Olympic flag?",                       ["4","5","6","7"],                                         1, "easy"),
        ("Which sport uses a shuttlecock?",                               ["Squash","Table tennis","Badminton","Racquetball"],       2, "easy"),
        ("In tennis, what is a score of zero called?",                    ["Nil","Love","Zero","Duck"],                              1, "easy"),
        ("How long is a marathon in miles (approximately)?",              ["18","22","26","30"],                                     2, "easy"),
        ("How many goals make a hat-trick?",                              ["2","3","4","5"],                                         1, "easy"),
        ("Which sport is played at Wimbledon?",                           ["Cricket","Squash","Tennis","Polo"],                     2, "easy"),
        ("How many points is a field goal worth in American football?",   ["1","2","3","4"],                                         2, "easy"),
        # ── MEDIUM (10) ────────────────────────────────────────────────────
        ("What is the maximum score in ten-pin bowling?",                 ["200","250","300","350"],                                 2, "medium"),
        ("Which country has won the most FIFA World Cups?",               ["Germany","Argentina","Italy","Brazil"],                  3, "medium"),
        ("What sport is associated with the Green Jacket?",               ["Tennis","Golf","Cricket","Polo"],                       1, "medium"),
        ("What country is credited with inventing cricket?",              ["Australia","India","England","South Africa"],            2, "medium"),
        ("How many points is a touchdown worth in American football?",    ["4","5","6","7"],                                         2, "medium"),
        ("How many players are in a volleyball team on the court?",       ["4","5","6","7"],                                         2, "medium"),
        ("In which country were the 2016 Summer Olympics held?",          ["China","UK","Brazil","Australia"],                       2, "medium"),
        ("What is the term for three consecutive strikes in bowling?",    ["Hat-trick","Triple","Turkey","Perfect"],                 2, "medium"),
        ("How many points is a basketball worth when shot from beyond the arc?",["1","2","3","4"],                                   2, "medium"),
        ("In baseball, how many strikes make an out?",                    ["2","3","4","5"],                                         1, "medium"),
        # ── HARD (10) ──────────────────────────────────────────────────────
        ("Which country won the first ever FIFA World Cup in 1930?",      ["Brazil","Argentina","Uruguay","Italy"],                  2, "hard"),
        ("What is the only Grand Slam tennis tournament played on clay?", ["Australian Open","Wimbledon","French Open","US Open"],  2, "hard"),
        ("In which year were women first allowed to compete in the Olympics?",["1896","1900","1908","1920"],                         1, "hard"),
        ("What is the highest possible break in snooker?",                ["140","147","150","155"],                                  1, "hard"),
        ("Which boxer was known as 'The Greatest'?",                      ["Mike Tyson","Muhammad Ali","Joe Frazier","Sugar Ray Leonard"], 1, "hard"),
        ("How many dimples does a standard golf ball have?",              ["252","336","392","420"],                                  1, "hard"),
        ("Which football club has won the most UEFA Champions League titles?",["Barcelona","Liverpool","Bayern Munich","Real Madrid"], 3, "hard"),
        ("How many times has Brazil won the FIFA World Cup?",             ["3","4","5","6"],                                         2, "hard"),
        ("In which year did Muhammad Ali defeat George Foreman in 'Rumble in the Jungle'?",["1972","1974","1976","1978"],           1, "hard"),
        ("What is the maximum number of sets in a Wimbledon men's singles match?",["3","4","5","6"],                                 2, "hard"),
    ],
}
# fmt: on


def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed old {DB_PATH}")

    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cat_id_map = {}
    for cat in CATEGORIES:
        cur.execute(
            "INSERT INTO categories (key, name, icon) VALUES (?, ?, ?)",
            (cat["key"], cat["name"], cat["icon"]),
        )
        cat_id_map[cat["key"]] = cur.lastrowid

    total = 0
    for cat_key, qs in QUESTIONS.items():
        cat_id = cat_id_map[cat_key]
        for q, opts, correct, diff in qs:
            cur.execute(
                """INSERT INTO questions
                   (category_id, question, option_0, option_1, option_2, option_3,
                    correct_index, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (cat_id, q, opts[0], opts[1], opts[2], opts[3], correct, diff),
            )
            total += 1

    conn.commit()
    conn.close()

    print(f"✅  Seeded {len(CATEGORIES)} categories, {total} questions into {DB_PATH}")
    for cat_key, qs in QUESTIONS.items():
        counts = {d: sum(1 for *_, diff in qs if diff == d) for d in ("easy","medium","hard")}
        print(f"   {cat_key:12s}  easy={counts['easy']}  medium={counts['medium']}  hard={counts['hard']}  total={len(qs)}")


if __name__ == "__main__":
    seed()

def seed_data():
    """Safe seed — only runs if categories table is empty (idempotent)."""
    from database import get_connection
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    conn.close()
    if count == 0:
        seed()
