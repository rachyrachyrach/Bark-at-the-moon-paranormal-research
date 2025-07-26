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

`moonphase --date 2025-07-26 --zip 10001`



output: 

`🌕 Full Moon on July 26, 2025 (New York, NY)
Moonrise: 8:23 PM, Moonset: 6:12 AM`



Run moonphase 7 days example: 

`moonphase --date 2025-07-20 --zip 43016 --days 7`


```
Moon Phases for Dublin, OH

2025-07-20   ◐   First Quarter (nearest on 2025-07-21)
2025-07-21   ○   Full Moon
2025-07-22   ○   Full Moon (nearest on 2025-07-21)
2025-07-23   ○   Full Moon (nearest on 2025-07-21)
2025-07-24   ○   Full Moon (nearest on 2025-07-21)
2025-07-25   ○   Full Moon (nearest on 2025-07-21)
2025-07-26   ○   Full Moon (nearest on 2025-07-21)
```