# ELG API for Aalto Finnish forced alignment pipeline

This git repository contains [ELG compatible](https://european-language-grid.readthedocs.io/en/stable/all/A3_API/LTInternalAPI.html)  Flask based REST API for the HeLI-OTS language identifier.

[Aalto-finn-forced-alginment](https://github.com/aalto-speech/finnish-forced-alignment) is a forced aligner for Finnish that can also be used in cross-language forced alignment. The tool is written in Python, and published under MIT license.
Original authors are Juho Leinonen, Sami Virpioja and Mikko Kurimo. Published paper available [here](https://helda.helsinki.fi/handle/10138/330758).

This ELG API was developed in EU's CEF project: [Microservices at your service](https://www.lingsoft.fi/en/microservices-at-your-service-bridging-gap-between-nlp-research-and-industry)


## Building the docker image

```
docker build -t finn-forced-aligner-elg .
```

Or pull directly ready-made image `docker pull lingsoft/finn-forced-aligner:tagname`.

## Deploying the service

```
docker run -d -p <port>:8000 --init --memory="2g" --restart always finn-forced-aligner-elg
```

## REST API
The ELG Audio service accepts POST requests of Content-Type: multipart/form-data with two parts, the first part with name “request” has type: `application/json`, and the second part with name “content” will be audio/x-wav type which contains the actual audio data with 16,000Hz sample rate.

### Call pattern

#### URL

```
http://<host>:<port>/process
```

Replace `<host>` and `<port>` with the host name and port where the 
service is running.

#### HEADERS

```
Content-type : multipart/form-data
```

#### BODY

```json
{
  "type":"audio",
  "format":"string", // LINEAR16 for WAV //required
  "sampleRate":number,
  "features":{ /* fname: "audio filename", "transcript": "text of the audio" */ }, //required
}
```

The `fname` key of `features` property of the body is optional but `transcript` key is required. Properties `format` and `sampleRate` are both required.

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

The script sends multipart/form-data POST request with the audio file under `src_for_txt/pohjantuuli_ja_aurinko.wav` and the corresponding script `src_for_txt/pohjantuuli_ja_aurinko.txt` 


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

