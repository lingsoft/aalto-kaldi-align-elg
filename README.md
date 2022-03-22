# ELG API for Aalto Finnish forced alignment pipeline

This git repository contains [ELG compatible](https://european-language-grid.readthedocs.io/en/stable/all/A3_API/LTInternalAPI.html)  Flask based REST API for the Finnish forced alignment.

[Aalto-finn-forced-alignment](https://github.com/aalto-speech/finnish-forced-alignment) is a forced aligner for Finnish that can also be used in cross-language forced alignment. The tool is written in Python, and published under MIT license.
Original authors are Juho Leinonen, Sami Virpioja and Mikko Kurimo. Published paper available [here](https://helda.helsinki.fi/handle/10138/330758).

This ELG API was developed in EU's CEF project: [Microservices at your service](https://www.lingsoft.fi/en/microservices-at-your-service-bridging-gap-between-nlp-research-and-industry)


## Building the docker image

```
docker build -t finn-forced-aligner-elg .
```

Or pull directly ready-made image `docker pull lingsoft/aalto-forced-aligner-fi:tagname`.

## Deploying the service

```
docker run -d -p <port>:8000 --init --memory="2g" --restart always finn-forced-aligner-elg
```
## Running tests
````
python3 -m unittest  -v
````

## REST API
The ELG Audio service accepts POST requests of Content-Type: multipart/form-data with two parts, the first part with name `request` has type: `application/json`, and the second part with name `content` will be audio/x-wav type which contains the actual audio data file.

### Call pattern

#### URL

```
http://<host>:<port>/process
```

Replace `<host>` and `<port>` with the hostname and port where the 
service is running.

#### HEADERS

```
Content-type : multipart/form-data
```

#### BODY

Part 1 with name `request`
```
{
  "type":"audio",
  "format":"string", // LINEAR16 for WAV //required
  "sampleRate":number,
  "features":{ /* fname: "audio filename", "transcript": "text of the audio" */ }, //required
}
```

The property `format` is required and `LINEAR16` value is expected, `sampleRate` is optional. In the property `features`, the `fname` key is optional but the `transcript` key is required. `transcript` should be the text that needs to be aligned with the audio in the second part.

Part 2 with name `content`
- read in audio file content
- maximum file size support: 25MB
- `WAV`format only, with an expected 16khz sample rate and a 16 bit sample size. Otherwise, the aligner will convert `WAV` file to a new file with 16khz sample rate and 16 bit sample size before aligning [Source](https://www.kielipankki.fi/tuki/aalto-asr-automaattinen-puheentunnistin/) (in Finnish only).
- can be either mono or stereo channels.


#### RESPONSE

```json
{
  "response":{
    "type":"annotations",
    "annotations":{
      "forced_alignment":[
   {
      "start":number,
      "end":number,
      "features":{
         "aligned":str
      }
   },
      ]
    }
  }
}
```

### Response structure

- `start` and `end` (float)
  - the time indices of the aligned word
- `aligned` (str)
  - the aligned word

### Example call

```
python3 multi_form_req.py
```

The script sends multipart/form-data POST request with the audio file under `src_for_txt/pohjantuuli_ja_aurinko.wav` and the corresponding script `src_for_txt/pohjantuuli_ja_aurinko.txt`. Also, there is another API call on a simple audio file `ikkuna.wav` which contains only one word 'ikkuna' after that. The audio file `ikkuna.wav` is converted from the mp3 version of `ikkuna.mp3` which is taken from [forvo](https://forvo.com/word/ikkuna/)

### Response should be
```json
{
  "response":{
    "type":"annotations",
    "annotations":{
      "forced_alignment":[
   {
      "start":"1.07",
      "end":"1.74",
      "features":{
         "aligned":"Pohjantuuli"
      }
   },
   {
      "start":"1.74",
      "end":"1.85",
      "features":{
         "aligned":"ja"
      }
   },
   {
      "start":"1.85",
      "end":"2.44",
      "features":{
         "aligned":"aurinko."
      }
   }, // truncated
  ]
    }
  }
}
```

