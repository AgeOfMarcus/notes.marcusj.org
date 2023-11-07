# [**Create an account**](/signup) to save and create multiple notes

### Scroll down to view new features

---

<button onclick='document.getElementById("num").innerText = (parseInt(document.getElementById("num").innerText) + 1).toString()'><b id='num'>0</b> Clicks</button>

![Edit me](https://i.marcusj.org/i/4)

# Host your images on [i.marcusj.org](https://i.marcusj.org)

## [Markdown Basic Syntax Guide](https://www.markdownguide.org/basic-syntax/ "Click Me")

<button onclick="doPOST('/click', {'id':'2d5a211a-c7b8-4eba-b264-3aadc5a15f0c'}, function(res) { document.getElementById('2d5a211a-c7b8-4eba-b264-3aadc5a15f0c').innerText = res['count'] } )"><span id='2d5a211a-c7b8-4eba-b264-3aadc5a15f0c'>x</span> likes</button>

---

# Changelog and features

---

### Create linked pages

Now, with a click of a button, anyone can view the [**document you just created**](https://notes.marcusj.org/link/df29c8b6485644e1b06685ee11446e87). Markdown and HTML gets rendered from your note and sent to their browser! When you update your note, the link gets updated too!

Optionally, create a link that returns the raw text of your note. This can be used to provide javascript or css files that change when you edit the source!

---

### Insert custom data

When editing a note, you can now use custom expressions. E.g. \{\{ date \}\} will be replaced with the current date upon saving the note. Below is a list of all expressions.

```
\{\{ date \}\} - current date
\{\{ time \}\} - current time
\{\{ js|yourcode \}\} - eval JS and place here. This JS get's executed every time you view the document. Will only work for links, not in-editor
\{\{ counter \}\} or \{\{ counter|text to display \}\} - a unique counter button embedded in your note. adds one every time it is clicked. only displays number of clicks after clicked
```

##### More will be added soon!

---

### MARKDOWN_EXTRAS

We use the `python-markdown2` package for compiling markdown on linked pages. These are the extras we use. You can view more about them [here](https://github.com/trentm/python-markdown2/wiki/Extras).

```
MARKDOWN_EXTRAS = [
    'spoiler',
    'strike',
    'task_list',
    'fenced-code-blocks',
    'header-ids',
    'markdown-in-html',
    'target-blank-links',
    'tables',
    'footnotes',
]
```