import sys
import os

# Add the project root to sys.path to import api.utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.utils import resolve_country_code

test_cases = [
    # NORTH AMERICA
    ("United States", "us"), ("Washington D.C.", "us"), ("New York", "us"), ("Los Angeles", "us"),
    ("Canada", "ca"), ("Ottawa", "ca"), ("Toronto", "ca"), ("Vancouver", "ca"),
    ("Mexico", "mx"), ("Mexico City", "mx"), ("Guadalajara", "mx"),
    ("Cuba", "cu"), ("Havana", "cu"), ("Guatemala City", "gt"), ("Haiti", "ht"), ("Port-au-Prince", "ht"),
    ("Dominican Republic", "do"), ("Santo Domingo", "do"), ("Kingston, Jamaica", "jm"), ("San Juan, Puerto Rico", "pr"),
    
    # EUROPE
    ("Germany", "de"), ("Deutschland", "de"), ("Berlin", "de"), ("Munich", "de"), ("Frankfurt", "de"),
    ("Ukraine", "ua"), ("Україна", "ua"), ("Kyiv", "ua"), ("Kharkiv", "ua"), ("Lviv", "ua"),
    ("United Kingdom", "gb"), ("London", "gb"), ("Manchester", "gb"), ("Glasgow", "gb"), ("England", "gb"),
    ("France", "fr"), ("Paris", "fr"), ("Lyon", "fr"), ("Marseille", "fr"),
    ("Italy", "it"), ("Rome", "it"), ("Milan", "it"), ("Naples", "it"),
    ("Spain", "es"), ("Madrid", "es"), ("Barcelona", "es"), ("Seville", "es"),
    ("Netherlands", "nl"), ("Amsterdam", "nl"), ("Rotterdam", "nl"), ("The Hague", "nl"),
    ("Poland", "pl"), ("Warsaw", "pl"), ("Krakow", "pl"), ("Gdansk", "pl"),
    ("Switzerland", "ch"), ("Bern", "ch"), ("Zurich", "ch"), ("Geneva", "ch"),
    ("Sweden", "se"), ("Stockholm", "se"), ("Gothenburg", "se"),
    ("Norway", "no"), ("Oslo", "no"), ("Bergen", "no"),
    ("Denmark", "dk"), ("Copenhagen", "dk"), ("Aarhus", "dk"),
    ("Finland", "fi"), ("Helsinki", "fi"), ("Espoo", "fi"),
    ("Austria", "at"), ("Vienna", "at"), ("Salzburg", "at"),
    ("Belgium", "be"), ("Brussels", "be"), ("Antwerp", "be"),
    ("Ireland", "ie"), ("Dublin", "ie"), ("Cork", "ie"),
    ("Portugal", "pt"), ("Lisbon", "pt"), ("Porto", "pt"),
    ("Greece", "gr"), ("Athens", "gr"), ("Thessaloniki", "gr"),
    ("Czechia", "cz"), ("Prague", "cz"), ("Brno", "cz"),
    ("Hungary", "hu"), ("Budapest", "hu"),
    ("Romania", "ro"), ("Bucharest", "ro"),
    ("Bulgaria", "bg"), ("Sofia", "bg"), ("Croatia", "hr"), ("Zagreb", "hr"),
    ("Russia", "ru"), ("Moscow", "ru"), ("Saint Petersburg", "ru"),
    
    # ASIA
    ("Japan", "jp"), ("日本", "jp"), ("Tokyo", "jp"), ("Osaka", "jp"),
    ("China", "cn"), ("中国", "cn"), ("Beijing", "cn"), ("Shanghai", "cn"), ("Shenzhen", "cn"),
    ("India", "in"), ("भारत", "in"), ("New Delhi", "in"), ("Mumbai", "in"), ("Bangalore", "in"),
    ("South Korea", "kr"), ("Seoul", "kr"), ("Busan", "kr"),
    ("Taiwan", "tw"), ("Taipei", "tw"), ("Indonesia", "id"), ("Jakarta", "id"),
    ("Vietnam", "vn"), ("Hanoi", "vn"), ("Ho Chi Minh City", "vn"),
    ("Philippines", "ph"), ("Manila", "ph"), ("Quezon City", "ph"),
    ("Thailand", "th"), ("Bangkok", "th"), ("Chiang Mai", "th"),
    ("Malaysia", "my"), ("Kuala Lumpur", "my"), ("Pakistan", "pk"), ("Karachi", "pk"),
    ("Singapore", "sg"), ("Iran", "ir"), ("Tehran", "ir"), ("Iraq", "iq"), ("Baghdad", "iq"),
    ("Saudi Arabia", "sa"), ("Riyadh", "sa"), ("Turkey", "tr"), ("Istanbul", "tr"), ("Ankara", "tr"),
    ("Israel", "il"), ("Jerusalem", "il"), ("Tel Aviv", "il"),
    ("United Arab Emirates", "ae"), ("Dubai", "ae"), ("Abu Dhabi", "ae"),
    ("Kazakhstan", "kz"), ("Almaty", "kz"),
    
    # AFRICA
    ("Nigeria", "ng"), ("Abuja", "ng"), ("Lagos", "ng"), ("Kano", "ng"), ("Ibadan", "ng"),
    ("Egypt", "eg"), ("Cairo", "eg"), ("Alexandria", "eg"), ("Giza", "eg"),
    ("South Africa", "za"), ("Pretoria", "za"), ("Johannesburg", "za"), ("Cape Town", "za"), ("Durban", "za"),
    ("Ethiopia", "et"), ("Addis Ababa", "et"), ("Kenya", "ke"), ("Nairobi", "ke"), ("Mombasa", "ke"),
    ("Morocco", "ma"), ("Rabat", "ma"), ("Casablanca", "ma"), ("Marrakesh", "ma"),
    ("Algeria", "dz"), ("Algiers", "dz"), ("Oran", "dz"),
    ("Ghana", "gh"), ("Accra", "gh"), ("Kumasi", "gh"), ("Ivory Coast", "ci"), ("Abidjan", "ci"),
    ("Uganda", "ug"), ("Kampala", "ug"), ("Sudan", "sd"), ("Khartoum", "sd"), ("Tanzania", "tz"), ("Dar es Salaam", "tz"),
    ("Angola", "ao"), ("Luanda", "ao"), ("Mozambique", "mz"), ("Maputo", "mz"), ("Madagascar", "mg"), ("Antananarivo", "mg"),
    ("Cameroon", "cm"), ("Douala", "cm"), ("Senegal", "sn"), ("Dakar", "sn"), ("Zimbabwe", "zw"), ("Harare", "zw"),
    ("Tunisia", "tn"), ("Tunis", "tn"), ("Libya", "ly"), ("Tripoli", "ly"), ("Mali", "ml"), ("Bamako", "ml"), ("Zambia", "zm"), ("Lusaka", "zm"),
    
    # SOUTH AMERICA
    ("Brazil", "br"), ("Brasilia", "br"), ("Sao Paulo", "br"), ("Rio de Janeiro", "br"),
    ("Argentina", "ar"), ("Buenos Aires", "ar"), ("Cordoba", "ar"),
    ("Colombia", "co"), ("Bogotá", "co"), ("Medellín", "co"),
    ("Peru", "pe"), ("Lima", "pe"), ("Arequipa", "pe"),
    ("Chile", "cl"), ("Santiago", "cl"), ("Venezuela", "ve"), ("Caracas", "ve"),
    ("Ecuador", "ec"), ("Quito", "ec"), ("Bolivia", "bo"), ("La Paz", "bo"), ("Uruguay", "uy"), ("Montevideo", "uy"),
    
    # OCEANIA
    ("Australia", "au"), ("Canberra", "au"), ("Sydney", "au"), ("Melbourne", "au"), ("Perth", "au"),
    ("New Zealand", "nz"), ("Wellington", "nz"), ("Auckland", "nz"),
    ("Fiji", "fj"), ("Suva", "fj"), ("Papua New Guinea", "pg"), ("Port Moresby", "pg"),
    
    # COMPLEX STRINGS
    ("Espoo region, Finland", "fi"),
    ("Melbourne, Australia", "au"),
    ("Auckland, New Zealand", "nz"),
    ("San Francisco, CA, USA", "us"),
    ("Berlin, Germany", "de"),
    ("Kyiv, Ukraine", "ua"),
    ("Tokyo, Japan", "jp"),
    ("Lagos, Nigeria", "ng"),
    ("Cairo, Egypt", "eg"),
    ("Johannesburg, South Africa", "za"),
    ("São Paulo, Brazil", "br"),
    ("Unknown Place", None),
]

passed = 0
failed = 0

print(f"{'Location':<30} | {'Expected':<8} | {'Actual':<8} | {'Status'}")
print("-" * 60)

for loc, expected in test_cases:
    actual = resolve_country_code(loc)
    status = "✅ PASS" if actual == expected else "❌ FAIL"
    if actual == expected:
        passed += 1
    else:
        failed += 1
    print(f"{loc:<30} | {str(expected):<8} | {str(actual):<8} | {status}")

print("-" * 60)
print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")

if failed > 0:
    sys.exit(1)
else:
    sys.exit(0)
