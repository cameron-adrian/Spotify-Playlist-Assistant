# TODO List

## High Priority

- [ ] Implement Oauth
- [ ] Refactor with React frontend?
- [ ]

## Medium Priority

- [ ]
- [ ]
- [ ]
- [ ]
- [ ]
- [ ]

## Low Priority

- [ ] Data visualization
- [ ]
- [ ]

## Need to learn more about:

1. Database architecture:
   - How should I be designing my models to be efficient?
   - What do I need to store and what do I need to call the Spotify API on demand for?
2. Best practices
   1. When should I serve what data to the user
   2. How to load data behind the scenes
   3. How to avoid the same operations/jobs more than necessary

# Design

### Basic Playlist Functionality

#### Outside the playlist (a list of playlists!)

1. LIST all of their playlists
   - AS A: SPA User
   - I WANT TO: Have all my playlists in a list
   - SO THAT: I can easily view see them all together
2. SORT all of their playlists

   - AS A: SPA User with playlists that each have different characteristics
   - I WANT TO: Sort my playlists by their characteristics
   - SO THAT: I can see my playlists in my desired order
   - Sort By:
     - total length
     - number of songs
     - alphabetically by title
     - most recently updated

3. FILTER all of their playlists
   - AS A: SPA User with playlists that each have different characteristics
   - I WANT TO: Filter out certain playlists by characteristics
     - Which characteristics?
     - Total Length?
     - Created at?
     - Updated at?
     - Average song length?
   - SO THAT: I can narrow which playlists I’m looking at

#### Inside the playlist

- URL Like: app/playlist-ID
- SORT songs by ALL Spotify characteristics
- FILTER songs by ALL Spotify characteristics

### Advanced Playlist Functionality

- Put playlists in folders (These would be MY folders, NOT Spotify’s, so possibly advanced wizardry?)
- Would I need to fully replicate the playback functions and stuff? This seems hard and inefficient, probably just use the webapp for organizing and then sending requests over to the desktop app, maybe be designed for them to be side by side?
- Click into a playlist and see the list of songs with all the extra characteristics that Spotify provides

#### Inside an individual playlist

- Sort by all characteristics
- Group by those characteristics
  - This would have to be categorical things? Idk how group by would work, I gotta think about this more
- Create custom tags
  - Applied at the song, playlist, or folder level?
  - Are they unique? Or can the same tag apply to each level of thing?
- Color coding
  - This would be like each decade/genre has a color
- Total playlist runtime at each song
  - Maybe have a “Will play at” column (enter time the party starts?)
- Alert if two songs by the same artist are gonna play too close together

### Nice to haves

##### “Transition Review Mode”

- Play the first X seconds of a song, then skip to the last Y seconds of the song and flow into the next one automatically

##### Heatmaps/gradients?

- How far from the designated parameter does each song in the playlist deviate?
  - Length, bpm, whatever

##### Data Viz

- Playlist growth over time (when were songs added)
  - Spotistats Plus after import ([outdated video](https://www.youtube.com/watch?v=5rIZW2zY27w))

### Open Questions

- Can you Update a spotify playlist? Or do you just have to create a new one each time?
- [Concerts and Festivals API from Songkick](https://www.songkick.com/developer)
  - Maybe pull the “fans also track” thing to make a playlist?
- Global Search Data Ideas
  - I should be able to sort all artists in the world by total plays, average plays of their top 10 songs, filter by country, genre, etc.
    - Like I could find out who the most popular people in mexico are, and break it down by all time or just the last year or whatever
- List an artists’ top songs by number of plays descending, across featured songs and originals
