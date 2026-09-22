# Lecture

## P005 — Driftwatch

*cybersecurity · cible 79/100 · rang 5 · RETENU*

**Source :** Upwind Security — 180 M$ Série A, visibilité cloud à l'exécution

```text
Driftwatch — runtime visibility for cloud workloads

THE PROBLEM

Cloud security tooling scans configuration and code. It tells you what could go wrong. It does not tell you what is happening right now inside a running container.

The result is alert volume nobody can act on. A typical platform team receives several thousand findings a month, of which a small fraction correspond to anything reachable in production. Teams learn to ignore the queue, which is the worst possible outcome for a security control.

OUR SOLUTION

Driftwatch observes workloads at runtime using eBPF probes, with no sidecar and no code change. We see which processes actually execute, which libraries are actually loaded, and which network paths are actually used.

That turns a static finding into a real one. A critical vulnerability in a library that is installed but never loaded is not an emergency; the same vulnerability in a library handling inbound requests is. We can tell the difference, and the difference typically removes 80 to 90% of a team's queue.

We also detect drift: a container whose running state diverges from the image it was built from, which is the signature of both a compromise and a bad deployment.

THE MARKET

Cloud workload protection is a $4.8B market growing at around 20% a year. It is crowded and consolidating, with several large platforms acquiring runtime capability rather than building it.

We sell to platform and security engineering teams in companies running more than 200 containers in production.

COMPETITION

The large cloud security platforms lead on breadth and on procurement. Their runtime components are generally bolted on and produce coarse signals. Several open-source projects cover parts of what we do, and we build on one of them.

Our differentiation is depth of runtime context and the correlation between what is running and what was scanned. We have published our probe overhead benchmarks, which competitors have not, because ours is under 1% of CPU and theirs is not.

THE TEAM

Tomas Eriksen and Nadia Belkacem met building platform infrastructure at a logistics company, where they ran the Kubernetes estate and built internal tooling that became the first version of this product.

Neither comes from a security background. We have hired two senior detection engineers to close that gap, and we treat it as a real one: our advantage is in systems engineering, not in threat research.

Sixteen people.

TRACTION

- 43 paying customers, including four with over 10,000 containers
- $2.8M annual recurring revenue, growing 9% month over month
- median alert volume reduction of 87% in the first month after deployment
- logo retention 95%, one churn in the last year
- 1,900 GitHub stars on our open-source probe library

BUSINESS MODEL

Consumption pricing based on monitored workload hours, with an annual commitment. Average contract value is $65,000. Gross margin is 79%.

Consumption billing aligns cost to value but makes revenue less predictable than seats; about a fifth of our customers vary more than 20% month to month.

GO-TO-MARKET

Inbound from the open-source library, converted by a small sales team. Average cycle is 11 weeks, extending to 20 for customers above 10,000 containers, where procurement and security review dominate.

FUNDING

We are raising $14M to build the detection content library, hire into threat research, and pursue the compliance certifications that enterprise procurement now requires.
```

## P006 — Remorq

*logistics · cible 78/100 · rang 6 · non retenu*

**Source :** Flock Freight — 215 M$ Série D, valo 1 Md$, mutualisation LTL. SLOT CRITIQUE : premier recalé, doit être franchement bon

```text
Remorq — pooled pallet freight across Western Europe

THE PROBLEM

One in four trucks in Europe runs empty, and those carrying cargo are on average only 63% full. Palletised freight — between 2 and 12 pallets, too little for a full truckload, too much for a parcel network — is where that waste concentrates.

A shipper sending 6 pallets has two options: pay for a full truck they will not fill, or use a traditional groupage network that multiplies handling. The second route means 4 to 7 handling steps, 3 to 5 days in transit, and a 2–4% damage rate.

OUR SOLUTION

Remorq pools shipments from several shippers onto the same truck, with no hub in between. Our matching engine reads incoming orders and builds two- or three-stop routes that stay economically viable for the carrier.

In practice: a shipper books 6 pallets from Lyon to Antwerp. In under two minutes the system finds two compatible shipments on time window and route, assembles the load and confirms a firm price. The goods never leave the truck between origin and destination.

THE MARKET

Palletised freight is worth roughly €38B a year in Western Europe. Most of it still moves through groupage networks run on the same principles as twenty years ago.

We are starting with France, the Benelux and western Germany — about €14B — where industrial density makes matching most effective.

COMPETITION

Incumbent groupage networks dominate the segment. Their strength is physical coverage; their weakness is the hub, which forces the handling steps. Several digital platforms offer on-demand full truckload, but none addresses palletised freight specifically.

We do not claim an unassailable technology: our matching engine builds on well-documented optimisation methods. Our lead comes from order-book density — the more simultaneous shipments, the better the matches — and from having started with the densest corridors.

THE TEAM

Claire Vanderbeke spent nine years running groupage operations at one of Europe's five largest carriers, with responsibility for 1,200 daily departures. Tomas Ruiz built and led the route optimisation team at a delivery platform operating in eleven countries. The two worked on this problem for eighteen months before incorporating.

We are fourteen people today, six of them in operations — this business does not fully automate on day one.

TRACTION

- 31 months of operation
- €34M billed volume over the last twelve months
- 7% month-on-month growth over the last six months
- 890 active shippers, 140 of them billing more than €15,000 per month
- 12-month retention: 86%
- average load factor: 84%, against an industry average of 63%
- 4,100 partner carriers

BUSINESS MODEL

We collect what the shipper pays and remit to the carrier. Gross take rate is 14%, which on last year's volume is €4.8M. After direct operating costs — support, claims handling, cargo insurance — 6.2 points remain, or €2.1M, up from 4.8 points a year ago.

We report billed volume and net contribution separately because they are not the same number and we would rather you did not have to work that out yourself.

That margin is structurally thin: we are a pass-through, and our revenue is a narrow slice of a large one. It improves as density grows, since the cost of processing a shipment falls when matching gets easier. We have not yet shown that it holds beyond our three main corridors.

GO-TO-MARKET

Direct sales to supply chain directors at mid-sized manufacturers. Average cycle of 7 weeks. Acquisition cost of €2,100 per active shipper, paid back in 4.5 months.

FUNDING

We are raising €12M to open three additional corridors, grow the operations team to fifteen, and industrialise the matching engine, which today is manually supervised beyond three stops.
```

