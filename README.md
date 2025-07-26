# Bark-at-the-moon-paranormal-research
For the [Boot.dev July 2025 Hackathon!](https://blog.boot.dev/news/hackathon-2025/)

Make your virtual environment

`python3 -m venv .venv`


Start your virtual environment 

`source .venv/bin/activate`


Install ephem 

`pip install ephem`


Move into the moonphase-cli directory 


```
cd moonphase-cli
```

Example of location:

```
/Users/rachael/github/Bark-at-the-moon-paranormal-research/moonphase-cli

```


Install moonphase-cli

```
pip install -e .

```




Run moonphase example: 

`moonphase --date 2025-07-26 --zip 43016`



output: 

```
🌕 Full Moon on 2025-07-26 for Dublin, OH
Illumination: 100.0%
Moonrise: 20:37, Moonset: 06:11
   ○
```



Run moonphase 7 days example: 

`moonphase --date 2025-07-20 --zip 43016 --days 7`


```
Moon Phases

Date         Phase               Illumination
------------------------------------------------------
2025-07-20   🌘 Waning Crescent        28.1%
2025-07-21   🌘 Waning Crescent        18.3%
2025-07-22   🌘 Waning Crescent        10.2%
2025-07-23   🌘 Waning Crescent         4.3%
2025-07-24   🌑 New Moon                1.0%
2025-07-25   🌑 New Moon                0.1%
2025-07-26   🌒 Waxing Crescent         1.8%
```