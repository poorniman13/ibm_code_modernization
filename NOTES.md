# What I checked, and what the agent got wrong

## What the agent got wrong

The agent initially used // for the wear calculation. This was wrong because it rounded the result down, so a car that had used 50% of its service interval could be shown as having 0% wear. I also noticed that the warning threshold had been changed from 80% to 85%, even though the original 80% rule was supposed to stay unchanged.

## What I checked before I accepted its work

I checked the wear calculation and made sure it uses normal division so the percentage is calculated correctly. I also checked that the warning threshold remained at 80%. Finally, I ran python verify.py and used the verification checks to confirm that the required changes were completed.

## What the data actually said

I compared the cars that broke down with the cars that did not. Total mileage and age were almost the same between the two groups, so they did not show a clear difference. The cars that broke down had higher distance since their last service and were worked harder. This showed that service distance and workload were more useful indicators of breakdown risk than total mileage or age.
