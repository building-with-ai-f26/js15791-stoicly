"""Verified Stoic quotes that Stoicly is allowed to show.

The model never writes quote text itself. It picks one of these ids, and the
server fills in the exact wording and source. This stops invented or
paraphrased "quotes" (e.g. the popular "You have power over your mind, not
outside events..." line, which is not in the Meditations).

Wording comes from public-domain translations:
  Marcus Aurelius, Meditations - George Long (1862)
  Epictetus, Enchiridion - T. W. Higginson (1865) / Elizabeth Carter (1758)
  Seneca, Moral Letters - R. M. Gummere (1917)
  Seneca, Moral Essays - J. W. Basore (1928/1932)

To add a quote: copy it exactly from a translation, add the source, and keep
the theme short (the model uses it to choose).
"""

QUOTES = {
    "control": {
        "text": "There are things which are within our power, and there are things which are beyond our power.",
        "author": "Epictetus",
        "source": "Enchiridion 1",
        "theme": "separating what you control from what you don't",
    },
    "opinions": {
        "text": "Men are disturbed not by things, but by the principles and notions which they form concerning things.",
        "author": "Epictetus",
        "source": "Enchiridion 5",
        "theme": "distress comes from our judgments, not events",
    },
    "accept_events": {
        "text": "Demand not that events should happen as you wish; but wish them to happen as they do happen, and you will go on well.",
        "author": "Epictetus",
        "source": "Enchiridion 8",
        "theme": "accepting outcomes, letting go of how things should go",
    },
    "judgement": {
        "text": "If thou art pained by any external thing, it is not this thing that disturbs thee, but thy own judgement about it. And it is in thy power to wipe out this judgement now.",
        "author": "Marcus Aurelius",
        "source": "Meditations 8.47",
        "theme": "hurt feelings, criticism, being upset by something outside you",
    },
    "obstacle": {
        "text": "That which is an obstacle on the road helps us on this road.",
        "author": "Marcus Aurelius",
        "source": "Meditations 5.20",
        "theme": "setbacks and obstacles as opportunities",
    },
    "difficult_people": {
        "text": "Begin the morning by saying to thyself, I shall meet with the busy-body, the ungrateful, arrogant, deceitful, envious, unsocial.",
        "author": "Marcus Aurelius",
        "source": "Meditations 2.1",
        "theme": "difficult or rude people, conflict at work",
    },
    "revenge": {
        "text": "The best way of avenging thyself is not to become like the wrong doer.",
        "author": "Marcus Aurelius",
        "source": "Meditations 6.6",
        "theme": "being wronged, wanting to get even",
    },
    "be_good": {
        "text": "No longer talk at all about the kind of man that a good man ought to be, but be such.",
        "author": "Marcus Aurelius",
        "source": "Meditations 10.16",
        "theme": "acting on values, self-improvement, stop overthinking",
    },
    "imagination": {
        "text": "We are more often frightened than hurt; and we suffer more from imagination than from reality.",
        "author": "Seneca",
        "source": "Moral Letters 13",
        "theme": "worry, anxiety about the future, catastrophizing",
    },
    "today": {
        "text": "Hold every hour in your grasp. Lay hold of to-day's task, and you will not need to depend so much upon to-morrow's.",
        "author": "Seneca",
        "source": "Moral Letters 1",
        "theme": "procrastination, focusing on today's work",
    },
    "time": {
        "text": "It is not that we have a short space of time, but that we waste much of it.",
        "author": "Seneca",
        "source": "On the Shortness of Life 1",
        "theme": "time, priorities, feeling there is never enough time",
    },
    "anger": {
        "text": "The greatest remedy for anger is delay.",
        "author": "Seneca",
        "source": "On Anger 2.29",
        "theme": "anger, frustration, wanting to react right away",
    },
}
