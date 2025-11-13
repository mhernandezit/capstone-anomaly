# Presentation Script

- **Title:** Machine Learning for Network Anomaly and Failure Detection  
- **Presenter:** Michael Hernandez  
- **Date:** Nov 9, 2025  

---

## Opening Line

> Imagine it’s 2 a.m. and your internet goes down. What broke, and how fast can we fix it?

---

## Slide 1: Cover  
*About 30–45 seconds*

Tonight I will show a simple way to spot network problems quickly and point to where they likely began. The goal is not to drown people in alerts. The goal is to give clear signals that help real teams fix real issues faster. I built and tested a small system that combines two kinds of information: how traffic paths change and how device health looks in that moment. When those move together, we act sooner with more confidence. That is the core idea we will walk through.

---

## Slide 2: Agenda  
*About 20–30 seconds*

Here is our plan. First, why this matters. Then the topic at a glance. Next, the problem with today’s tools. I will explain the solution in plain terms, share what we found in a lab test, and close with limits and next steps. Full references are at the end, and the paper has the math and details.

---

## Slide 3: Why this matters  
*About 45–60 seconds*

Outages cost people time, sleep, and trust. Operators get paged again and again, and many alerts do not help. They point everywhere and nowhere. What teams need are signals that say two things clearly: something unusual is happening and here is the most likely place to start looking. When that happens, triage speeds up. The right person gets involved. Customers feel the difference because service returns faster. That is the real outcome we are after.

---

## Slide 4: Goal  
*About 40–50 seconds*

The project has three simple goals. First, detect issues earlier than a human who is scanning dashboards. Second, show a likely starting point so the team knows where to focus. Third, cut false alarms so people trust the alerts they do receive. If the system cannot do those three things, it is not useful. Everything in this talk supports those goals.

---

## Slide 5: The signals we use  
*About 50–60 seconds*

We watch two things at the same time. One is how traffic paths change. When the network reroutes around trouble, paths shift. The other is device health, such as error counts or load. When equipment struggles, those numbers move. If path shifts and device health changes happen together in the same window of time and in the same neighborhood of the network, the chance that it is a real problem goes up. That joint movement is the signal we are after.

---

## Slide 6: Patterns versus surprises  
*About 45–60 seconds*

Most days have a steady rhythm. Traffic rises and falls in ways that repeat. Devices have normal ranges. Breaks do not look like that. Breaks leave fingerprints. You see sudden spikes or drops, and they often line up across sources. The approach here is simple. Learn what normal looks like and then watch for surprises. When two independent sources show surprises at the same time, we raise our hand and say this is worth a look.

---

## Slide 7: Why this topic  
*About 30–45 seconds*

I chose this problem because alert fatigue is real. Teams are already working hard. The answer is not more alerts. The answer is better triage. Combine signals, add a little context about where devices sit in the network, and bring the most important issues to the top. Small, practical changes can make a big difference in response time.

---

## Slide 8: What’s broken today  
*About 50–60 seconds*

Today many tools do not talk to each other. Routing events live in one place. Device health lives in another. People act as the glue between screens. There is also very little sense of blast radius. A hiccup at a core device is not the same as a hiccup at a leaf. Yet many alerts treat them the same way. Finally, fixed thresholds ignore context. They miss slow burns and cry wolf on routine peaks. These gaps create noise and slow down triage.

---

## Slide 9: Impact  
*About 40–50 seconds*

What is the cost of those gaps? Slow hunts. Missed patterns. Longer fixes. The team spends minutes, then hours, stitching together a story by hand. Confidence drops. When the next alert fires, people are less sure it matters. Customers notice the delay. Our focus, then, is to reduce that time from first page to first good clue.

---

## Slide 10: What we need  
*About 45–60 seconds*

We need three things. First, combine signals so each incident has one clear story. Second, understand the basic map of the network. A problem at the core reaches farther than a problem at the edge. Third, prioritize by likely impact. Show fewer alerts, but make them better. When the top of the queue contains the few items that truly matter, people move faster with less stress.

---

## Slide 11: How it works  
*About 60–75 seconds*

Here is the system in plain terms. We stream path changes and device health as they happen. We look for behavior that does not fit the recent baseline. We then fuse the two sources. If both say “this looks unusual” at the same time and in the same neighborhood, we score it higher. The output is a short alert that fits in a single screen. It points to a likely starting point and includes a small note on why it is likely. The intent is to save the operator those first few minutes of guesswork.

---

## Slide 12: Two key views  
*About 40–50 seconds*

Think of it as two simple views. View one shows traffic paths. Are they shifting here and now. View two shows device health nearby. Is a device showing strain here and now. If both move together, we have a solid lead. If only one moves, we hold back and look for more evidence. That restraint helps reduce false alarms.

---

## Slide 13: Triage that knows the map  
*About 45–60 seconds*

Not all devices are equal. A problem at a core switch can affect many more people than a problem at an edge. So the system includes a simple map of roles. Core and aggregation sit higher. Edge and access sit lower. We combine that with a rough idea of downstream reach. The score rises when the blast radius is bigger. The result is a list that puts higher impact items first. That is how we aim for fewer, better alerts.

---

## Slide 14: How we tested  
*About 45–60 seconds*

We tested this in a small lab. Most of the time the traffic was normal. We injected a handful of real faults. We measured two things. One was how quickly the system noticed. The other was how noisy the alerts were. We care about speed, but only if the signal is trusted. If the system pages often and is wrong, people will stop listening. So both speed and trust matter.

---

## Slide 15: What we found  
*About 60–75 seconds*

In the lab we found issues in well under a minute on average. The alert count dropped when we combined signals, compared to fixed thresholds. Most important, the alerts were clearer. They said what changed, where to look first, and why this was likely real. That clarity shortened the time to a good first action. In practice that means less time staring at dashboards and more time fixing the right thing.

---

## Slide 16: Limits and next steps  
*About 60–75 seconds*

This is a lab result, not a field trial. Real networks are messier. The next steps are straightforward. First, try more types of faults, especially slow degradations. Second, replay real captures to see how the system behaves under pressure. Third, scale the topology and watch the cost and stability over time. If the signal stays strong under those conditions, we will have evidence that this simple approach helps in the real world.

---

## Slide 17: References 1 of 2  
*About 20–30 seconds*

You will find the full references here. The paper includes full citations and links for those who want to dive deeper into time series pattern search, outlier detection, and routing fundamentals.

---

## Slide 18: References 2 of 2  
*About 20–30 seconds*

These sources also influenced the design choices and the way we evaluated the system. I am happy to share the paper and code details with anyone who is interested after the talk.

---

## Closing Line

> Combine the right signals, focus on what matters, and we fix outages faster. Thank you.

---

## Optional Q&A Bridge

If there are questions, I can start with how we aligned timing windows across sources, or how the priority score balances location and impact.
