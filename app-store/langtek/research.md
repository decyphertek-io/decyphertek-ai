

* pyttsx3 _ This will use Local , Except the issue is local isnt very good? ( Maybe can use an Offline Model? )
* GTTS - Works well , except not offline 

Focus Just on Speech SYnthesis
# Dont use installs nvidia and cuda coqui-tts

import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Print the list of available voices
for i, voice in enumerate(voices):
    print(f"{i}: {voice.name} — {voice.id}")

# Set the desired voice (e.g., with index 1)
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 150)
engine.setProperty('volume', 1)

engine.say("Hello! This is the Microsoft Natural Voice.")
engine.runAndWait()

============




import argostranslate.package
import argostranslate.translate

from_code = "es"
to_code = "en"

# Download and install Argos Translate package
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
package_to_install = next(
    filter(
        lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
    )
)
argostranslate.package.install_from_path(package_to_install.download())

# Translate
translatedText = argostranslate.translate.translate("Hello World", from_code, to_code)
print(translatedText)
# '¡Hola Mundo!'







==========


Libretrasnalte api
const res = await fetch("https://translate.argosopentech.com/translate", {
    method: "POST",
    body: JSON.stringify({
        q: "Hello!",
        source: "en",
        target: "es"
    }),
    headers: {
        "Content-Type": "application/json"}
    });

console.log(await res.json());

// {
//    "translatedText": "¡Hola!"
// }