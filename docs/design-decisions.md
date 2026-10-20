FlowForge Design Decisions

Why I built it this way, what I skipped, and what can wait. I’ll add to this as I go.

Architecture

Serverless.
I don’t want to pay for or patch a server that sits there doing nothing. Lambda, DynamoDB, and API Gateway work for what I’m building. I didn’t have a reason to use EC2 here.

Terraform for everything.
I want to be able to rebuild this without trying to remember every setting I clicked. The code is there, and Git shows me what changed.

Terraform state stays on my laptop for now.
It’s just me working on this. The state file can contain sensitive information, so it does not go to GitHub. Moving it to S3 is on my list.

Data

DynamoDB on-demand.
I don’t know how many people will use this yet. I’m not going to guess at capacity before I have traffic.

Scan, then filter in Python.
The poses table is small. Scanning it and filtering by body area and difficulty works for now. If it grows enough to need an index, I’ll revisit it.

API

HTTP API instead of REST API.
I’m using HTTP API because it costs less and has what I need. I don’t need API keys or usage plans for this version.

POST /flow.
I send the preferences in the request body, and the app builds a random flow from them. That felt straightforward, especially when someone picks more than one body area.

Let the Lambda handle the request.
I’m using proxy integration so my Python code handles the input, response, and status codes. No mapping templates to set up.

Check the input.
The API is public, so I can’t assume people will send what I expect. A bad request should get a 400 with a useful message. It shouldn’t crash the Lambda.

60-minute max.
There needs to be a limit. Nobody needs to ask this public endpoint for a 9,000-minute yoga flow.

5 requests a second, burst of 10.
There’s no login, so I added throttling to help limit traffic and unnecessary costs. It won’t stop everything, but I wanted that limit in place.

CORS is open for now.
The frontend isn’t hosted yet. Once it’s on CloudFront, I’ll restrict the allowed origin to that domain.

Logs stay for 14 days.
Enough to debug. I’m not paying to keep them forever.

10-second timeout.
I gave the Lambda more room than the default three seconds for startup and scanning the table. I’ll see what the actual request times look like before changing it.

Security

The Lambda can only Scan the poses table.
It needs to read poses. It has no reason to add, change, or delete them.

No accounts in V1.
You can generate a flow without making an account, and I’m not saving personal information. If I add saved flows, I’ll bring in Cognito.

textContent for pose names from the API.
V1 only shows pose names. Instructions are planned for later. I’m using textContent so the browser displays those names as text instead of interpreting them as HTML.

Frontend

Plain HTML, CSS, and JavaScript.
I have enough to learn on the AWS side. I didn’t want to add React to the list just to build this frontend. No build step, either. The files I write are the files I deploy.

The timer uses an end time.
Counting down one second at a time can drift if the browser delays an update. I calculate what’s left from the end time so those delays don’t keep adding up.

Per-side poses get two steps.
I want the timer to tell me when to switch sides. Otherwise, I’m doing yoga and keeping track of the halfway point in my head. I’d rather let the timer handle it.