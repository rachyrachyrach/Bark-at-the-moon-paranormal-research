# Bark-at-the-moon-paranormal-research
For the [Boot.dev July 2025 Hackathon!](https://blog.boot.dev/news/hackathon-2025/)

[![Bark-at-the-moon-paranormal-research](http://img.youtube.com/vi/D_IhfJpjxl8/0.jpg)](http://www.youtube.com/watch?v=D_IhfJpjxl8 "Bark-at-the-moon-paranormal-research")




I run a paranormal group for 15+ years called [TOPS](http://www.tennesseeohioparanormalsociety.com/).  We love using tech to help us in our research.  I like to save data
on locations and the environment.    This small script is to record what the current moon phase in at the location and crime data.  


I'm a skeptic and believe "Correlation does not imply causation" but it's still fun to look at the data. 




## Install

Make your virtual environment

`python3 -m venv .venv`

##

Start your virtual environment 

`source .venv/bin/activate`

##

Install [ephem](https://rhodesmill.org/pyephem/) and [InquirerPy](https://github.com/CITGuru/InquirerPy) rich Jinja2

`pip install ephem InquirerPy rich Jinja2`

##
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


# Run moonphase: 

Just type moonphase or watch the [video](https://www.youtube.com/watch?v=D_IhfJpjxl8)

`moonphase`

You'll be prompted for date, zipcode, 1 day or 7 days and save html file. 



Other options, you can type in a set date:

`moonphase --date 2025-07-26 --zip 43016`


output: 

```
🌕 Full Moon on 2025-07-26 for Dublin, OH
Illumination: 100.0%
Moonrise: 20:37, Moonset: 06:11
   ○
```



Run moonphase 7 days example: 

`moonphase --date 2025-07-26 --zip 43016 --days 7`


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


# For the Crime data:

_please note I ran out of time and can only display data by year._


1. You will need an api key. It is free on [Gov api](https://api.data.gov/signup/)


2. add your api locally

`export FBI_API_KEY="your-api-key-here"`


 This is the source of the crime data [FBI Crime data explorer](https://cde.ucr.cjis.gov/). The [api](https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/docApi)


Here is an example api endpoint

`https://api.usa.gov/crime/fbi/sapi/api/summarized/state/{state_abbr}/violent-crime/{start_year}/{end_year}?api_key=YOUR_KEY`


 Personally I use county level data for research but for the the bootdev hackathon, I wanted to keep it simple. 

 When we are on an investigation, we run [property searches](https://www.tennesseeohioparanormalsociety.com/research-property-search-public-records-by-using-osint/) and then you can search for the indicents in the news or county records. 



 Example of output from the crime api: 
 ![Chart](https://github.com/rachyrachyrach/Bark-at-the-moon-paranormal-research/blob/main/docs/fbi_api.jpg)