# Blog Structure

This directory contains the project blog for documenting design decisions, technical approaches, and lessons learned.

## Structure

```
docs/blog/
├── index.html          # Main blog listing page
├── post-template.html  # Template for new posts
├── posts/             # Individual blog posts
│   └── *.html         # Post files
└── README.md          # This file
```

## Writing a New Post

### Option 1: Write in Markdown (Recommended for Jekyll migration)

1. Create a new file in `posts/` with naming convention: `YYYY-MM-DD-title.md`
2. Add front matter:
```markdown
---
title: "Your Post Title"
date: 2026-01-09
tags: [automation, ev, github-actions]
excerpt: "A brief description of the post"
---

# Your Post Title

Your content here...
```

3. Convert to HTML using a Markdown processor or manually copy into `post-template.html`

### Option 2: Write Directly in HTML

1. Copy `post-template.html` to `posts/your-post-name.html`
2. Update the title, date, tags, and content
3. Add entry to `index.html` posts array:

```javascript
const posts = [
    {
        title: "Your Post Title",
        date: "2026-01-09",
        slug: "your-post-name",
        excerpt: "Brief description...",
        tags: ["tag1", "tag2"]
    }
];
```

## Future Jekyll Migration

To migrate to Jekyll later:

1. Install Jekyll: `gem install jekyll bundler`
2. Create `_config.yml` in repo root
3. Move posts to `_posts/` directory
4. Rename to Jekyll format: `YYYY-MM-DD-title.md`
5. Enable Jekyll in GitHub Pages settings

Markdown posts written now will work directly with Jekyll!

## Style Guide

- Match dashboard purple gradient theme
- Use code blocks for technical content
- Include clear section headers
- Add tags for categorization
- Keep excerpts under 200 characters
