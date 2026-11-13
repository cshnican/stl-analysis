# Share the Love analysis

Share the Love (STL) is a monthly, Eurovision-style fan contest. Each participant is a Head of Delegation and enters songs for countries. Voters give the Eurovision card once each: 12, 10, 8, 7, 6, 5, 4, 3, 2, and 1. This repository holds the results through STL 63, the ballots that could be read, and a static website that walks through them.

## Website

The pages are HTML files in the project folder. Open `index.html` in a browser. They share one paper-and-ink design, follow the system light or dark setting, and work on a phone. The front page links to the scoreboard and the song map. From a song, the head of delegation’s name and the country open their pages, and an artist credited on at least three songs opens theirs.

Place on the scoreboard, the head-of-delegation page, the country page, the artist page, and the medal table is the tie-break rank in that edition’s full field. The tie-break is higher jury points, then more 12s, then more 10s, then more 8s, then more 7s down through 1. When two songs match at every point value, the song earlier in the running order places higher. For an edition whose ballot stops at 12, 10, and 8, the countback stops there and the published order is kept. The rank number stays the tie-break rank when a table is sorted again.

Eurovision-scale points put a jury total on a 1,008-point scale. The score is 1,008 times the song’s percentage of the maximum vote, rounded half up to the nearest point. 1,008 is the maximum from 42 voting countries giving 24 points each. The percentage is the “% of the Maximum Vote” column in `data/entry_data.csv`.

### Front page

`index.html` introduces the contest. It links to the scoreboard and to the page that shows where the songs come from.

### Scoreboard

`scoreboard.html` shows one edition at a time, STL 1 through STL 63. The edition menu includes the date, written as day, month, and year, as in “STL 60 · 2 August 2026”.

Each row is a song. The columns are rank, song, jury points, Eurovision-scale points, and, when a ballot is on file, one column per voter. Click a heading to sort. The first click on a points column puts the highest score first, and the next click reverses it. Songs with equal points fall back to the tie-break rank. Click `#` to restore the tie-break order, and click `#` again to reverse the ranks. On a phone, the same sort is a menu and a direction button. Changing the edition clears the sort.

A head-of-delegation control keeps only the songs that person entered. The place shown is still their tie-break place in the full field, and the filter stays on while you change edition. When they entered no song, the page says so.

A song title with a known video links to YouTube. Voter headings sort the songs by the points that person gave. Egon and Pieter voted a full card in STL 60 and have entered no song, so they appear as voter columns. Georga voted in STL 47, 57, 58, and 63 and has entered no song. The STL 63 grid was read from the results image.

Complete ballots are on file for STL 1–14, 28, 32–36, 38–48, 50, 51, 53–60, 62, and 63. STL 15–27, 29–31, 37, 49, 52, and 61 show the ranked result with the points, the 12s, the 10s, and the 8s.

### Where songs come from

`song-distribution.html` covers the 1,845 songs in editions 1–63: 22 heads of delegation and 131 countries. Each edition has at most one song per country. The page has five views.

- Artists with at least two songs, ordered by average Eurovision-scale points. A collaboration counts for every named artist who also has their own credit. Credits that differ by case or accents are one artist.
- The twenty songs with the highest Eurovision-scale points.
- A grid of song counts, with heads of delegation down the rows and countries across the columns.
- A map shaded by each country’s best published place. A first place is the darkest. Click, tap, or hover a country to read the song, the artist, and the head of delegation. When several songs share that place, the one with more Eurovision-scale points is shown, and a later edition breaks a remaining tie. England, Scotland, Wales, Northern Ireland, and Malta are dots. Pinch or use the buttons to zoom, then drag to move the map.
- The eight head-of-delegation and country pairs with the most songs.

### Heads of delegation, countries, and artists

`hod.html` lists every song one head of delegation entered, with the tie-break place, the jury points, and the Eurovision-scale points. A map shades the countries where that person has entered songs. Click a country for the five highest Eurovision-scale scores there. The country name opens every song from that country.

`country.html` lists every song entered for one country, with the same place and points.

`artist.html` lists the 157 artists credited on at least three songs. A collaboration is listed for every named artist who also has their own credit. Credits that differ by case or accents are one artist, including Evangelia and Ευαγγελία, and Malou is counted with Malu. A song is included when the artist’s name is a name in the credit. The credit is split on a comma, `&`, `+`, feat., ft., and, a spaced slash, and a spaced x, including the Cyrillic letter х. These credits are kept as one name: Sophie and the Giants, Of Monsters And Men, Christine and the Queens, Florence + The Machine, Tones and I, and Cali y El Dandee. AU/RA, HUNTR/X, Allie X, and RY X stay one name because the slash or the X has no space beside it.

`medal-table.html` counts a gold medal for first place, silver for second, and bronze for third, using the same tie-break. Heads of delegation are ordered by gold, then silver, then bronze. Equal medal counts share a rank, and one edition can give the same person more than one medal. This page stands apart from the front page, the scoreboard, and the song map.

## Dataset

`data/entry_data.csv` is the published result for every song in STL 1–63. It has 1,845 rows, from 22 to 34 songs in an edition. The 22 heads of delegation who have entered a song are Alex, Anita, Chris, Danny, Dominik, Guilherme, Hanna, Harry, Ioannis, Jana, João, Lukas, Matthew, Nurti, Oisín, Ori, Paolo, Polly, SQ, Sandra, Sihan, and Twan. The columns are Edition, Code, Head of Delegation, Country, Song, Artist, Placing, Points, 12 points, 10 points, 8 points, RO Position, # of HODs Voting, % of HODs Voting, Average Points Given, % of the Maximum Vote, and % of the Total Vote. Placing is the published place. Country text is stored as published and can include a flag symbol. The pages calculate the tie-break rank from these points and, where a full ballot exists, from every point value.

`data/STL screenshot ballots.csv` has one row for each point a voter gave: 3,670 rows for editions 28, 33–36, 38–48, 50, 51, 53–56, 60, and 62. The columns are Edition, Code, HOD (the voter), Receiving HOD, Receiving Country, and Points. Blank cells are omitted. The file is UTF-8 with a byte-order mark, and each line ends with a carriage return and a line feed. `scripts/extract_votes.py` writes this file. The procedure is in [How the vote script works](#how-the-vote-script-works). The STL 60 rows include the guest voters Egon and Pieter.

`data/STL group contest stats 2.csv` is an earlier compiled sheet of 6,670 vote rows, each marked manual or automatic in a source column. It covers editions 1–14, 28–48, 50, 51, 53, 55–60, and 62. Where the scoreboard and this sheet both have a full ballot, the votes match, with two exceptions. In STL 57 the sheet writes Dominik as Dom. In STL 60 the sheet gives Harry’s Australia song a 6 from Matthew, and the scoreboard gives that 6 to Hanna. Editions 29, 30, 31, and 37 contain cards that are short of the full point list, and the scoreboard shows those editions as a ranked result. STL 54 is absent from this sheet. Its grid, and the checked STL 60 grid, are in the screenshot ballot file. The STL 63 grid is stored on the scoreboard page, read from the results image.

`data/master_sheet.csv` joins vote rows to the receiving song, the artist, a Spotify id, and audio features. It has 3,940 rows across 27 editions.

`data/song_info.csv` holds 1,778 Spotify track ids. `data/audio_features.csv` has one row per entry for editions 1–62 (1,814 rows): acousticness, danceability, energy, instrumentalness, key, liveness, loudness, mode, speechiness, tempo, and valence. `scripts/fetch_audio_features.py` writes it. The measures come from ReccoBeats, which returns the same fields, and some rows are filled from `data/ShareTheLove.csv`, a Spotify export of 1,190 tracks.

`data/my_stats.csv` and `data/my_stats.numbers` are a personal list of 86 songs from STL 1–43, with year, running order, country, result, and points. `scripts/my_stl.R` charts that list against the Spotify export.

## Changelog

The list follows the commits on `main`, newest first.

### 12 November 2026

- `5f5198e` — Open a country’s songs when the map is clicked on desktop, on the head-of-delegation map and on the best-result map.

### 11 November 2026

- `3dd9892` — Show each edition’s date on the scoreboard.
- `88fc331` — Add the STL 60 ballot, including guest voters Egon and Pieter.
- `11eed88` — Count Artem Pivovarov’s Cyrillic-x collaboration, and treat Malou as Malu.
- `866c4bf` — Add a page for every artist credited on at least three songs.
- `20619b6` — Add the STL 54 ballot so the scoreboard can show every vote.
- `2de43e0` — Add a front page that introduces Share the Love and leads to the scoreboard and the song map. The scoreboard moves to `scoreboard.html`.
- `1200cf4` — Show each song’s Eurovision-scale points beside the jury total on the scoreboard.
- `d9452e8` — Add a page of every song entered for a country.
- `6297f72` — Show a country’s top songs on the head-of-delegation map after a click.

### 10 November 2026

- `1f31adf` — Show each head of delegation’s song map on their own page.
- `334708d` — Show each song’s Eurovision-scale points on the head-of-delegation page.
- `02f5af7` — Add a sortable page of each head of delegation’s songs.
- `d1e7205` — Add a medal table, and correct Alex and Anita’s STL 62 votes in the stats sheet.
- `97d2ea2` — Swap Alex and Anita’s votes in STL 62.
- `af9e079` — Link scoreboard songs to their YouTube videos, and restore the song-map link.

### 9 November 2026

- `f3b3ac6` — Make the song maps usable on a phone.
- `d689f2e` — Merge pull request #2, bringing the restyled song page onto `main`.
- `92d4917` — Match the song page to the scoreboard and link the two pages.
- `17e700d` — Merge pull request #1, bringing the head-of-delegation filter onto `main`.
- `28288f7` — Filter each edition to one head of delegation’s songs.
- `a1967d2` — Serve the scoreboard as the site index.
- `e5a28cf` — Publish the STL analysis through edition 63, with the scoreboard, the song map, the results, the ballots, and the vote script.

# How the vote script works

This section tells you how the vote script works. The words in this section follow ASD-STE100, Simplified Technical English. The vote script is `scripts/extract_votes.py`. The script builds two programs that read the screenshot images.

## Contents

- [1. Purpose](#1-purpose)
- [2. Files and lists](#2-files-and-lists)
  - [2.1 Files that the script reads](#21-files-that-the-script-reads)
  - [2.2 File that the script writes](#22-file-that-the-script-writes)
- [3. Start the script](#3-start-the-script)
- [4. How the script reads one edition](#4-how-the-script-reads-one-edition)
  - [4.1 Find the table lines](#41-find-the-table-lines)
  - [4.2 Read the point value in each cell](#42-read-the-point-value-in-each-cell)
  - [4.3 Make each column the same as the point card](#43-make-each-column-the-same-as-the-point-card)
  - [4.4 Find the song for each row](#44-find-the-song-for-each-row)
  - [4.5 Find the voter for each column](#45-find-the-voter-for-each-column)
  - [4.6 Prepare the ballot rows](#46-prepare-the-ballot-rows)
- [5. Ballot file](#5-ballot-file)

## 1. Purpose

Share The Love is the song contest. ScoreWiz is the program that shows the results. A screenshot is a picture of the ScoreWiz results. Each screenshot is one edition. An edition is one contest. The files use the short name STL with the edition number. For example, STL41 is edition 41.

Each column of the results table is one voter. A voter is a Head of Delegation. The data files use the short name HOD for Head of Delegation. Each row of the results table is one song. Each cell shows the points that the voter gave to that song. An empty cell means that the voter gave no points to that song.

Each voter gives each of these point values one time:

```text
12, 10, 8, 7, 6, 5, 4, 3, 2, 1
```

The sum of these point values is 58. The script writes one row for each vote in the ballot file `data/STL screenshot ballots.csv`.

A score pattern has four numbers for one song.

- The first number is the total points.
- The second number counts the votes of 12 points.
- The third number counts the votes of 10 points.
- The fourth number counts the votes of 8 points.

For example, the score pattern `63, 2, 2, 1` means 63 points. That song also has two votes of 12 points and two votes of 10 points. It has one vote of 8 points.

## 2. Files and lists

### 2.1 Files that the script reads

| File | Contents |
| --- | --- |
| `scripts/extract_votes.py` | The main script |
| `scripts/grid_lines.m` | Source of the program that finds the table lines |
| `scripts/read_grid.m` | Source of the program that reads the digits |
| `data/entry_data.csv` | The published results for each song |
| `results_screenshots/STL41.jpg` | The template image for the digit shapes |
| `results_screenshots/STLn.jpg` | The screenshot for edition n |

A screenshot name can end with `.jpg` or with `.jpeg`. The template shows the font STL41. A font is the shape of the digits on the screen.

The script keeps four lists in `extract_votes.py`.

#### NAMES

This list holds the nickname at the top of each column, from left to right. A person copies these nicknames from the screenshot. Each edition in NAMES must have rows in `data/entry_data.csv`.

#### ALIAS

This list pairs a short nickname with a voter name. For example, the nickname `pol` is the voter Polly. The script changes the nickname to lower case before it reads ALIAS. It removes every period at the end of the nickname.

#### CONFIRMED

This list supplies a voter name when the nickname belongs to a different voter. It also supplies a name when more than one voter can fit the column.

#### TIE

This list gives the country for a row when two or more songs have the same score pattern. The row numbers in TIE start at 0. Row 0 is the first song row. The countries in TIE are in the simple form from [section 4.4](#44-find-the-song-for-each-row).

### 2.2 File that the script writes

The ballot file is `data/STL screenshot ballots.csv`. [Section 5](#5-ballot-file) gives the fields in this file.

## 3. Start the script

- The computer must use macOS.
- Python 3 must be on the computer.
- clang is the program that builds the two image programs.
- clang must be on the computer.

Put the screenshots in the folder `results_screenshots`.

At the start, the script builds two temporary programs. It builds them from `grid_lines.m` and `read_grid.m`. The two programs use macOS to open the images. The script builds the programs again on each start.

1. Open a Terminal window in the project folder.
2. Enter this command to read every edition in the NAMES list:

   ```bash
   python3 scripts/extract_votes.py
   ```

3. Add the edition numbers to read only those editions:

   ```bash
   python3 scripts/extract_votes.py 39 43
   ```

> [!CAUTION]
> `--write` replaces the ballot file when at least one edition passed. The new file has only the editions that passed in that run. Read every edition in NAMES when the full ballot file must be kept.

4. Put `--write` in the command when the script must write the ballot file.

   ```bash
   python3 scripts/extract_votes.py --write
   ```

You can put edition numbers and `--write` in the same command.

The script shows one status line for each edition. The line gives the number of voters with a name and the number of columns. If a column has no voter name, the next lines show that nickname. Those lines also show the voters that can still fit the column. The script prepares ballot rows for an edition only when every column has one voter.

In these cases, the script shows a short error and continues with the next edition:

- The edition is not in the NAMES list. The text is `no column names recorded`.
- There is no screenshot file. The text is `no screenshot`.
- No table passes the tests in [section 4.3](#43-make-each-column-the-same-as-the-point-card). The text is `grid does not match the results`.

If the script cannot find exactly one song for a row, it stops. The ballot file stays unchanged when the script stops for this reason. [Section 4](#4-how-the-script-reads-one-edition) tells you how each of these results happens.

## 4. How the script reads one edition

The script does these steps for each edition:

1. It finds the table lines in the screenshot.
2. It reads the point value in each cell.
3. It makes each column the same as the point card when [section 4.3](#43-make-each-column-the-same-as-the-point-card) accepts the change.
4. It finds the song for each row.
5. It finds the voter for each column.
6. It prepares one ballot row for each vote.

The point card is the ten point values `1, 2, 3, 4, 5, 6, 7, 8, 10, 12`.

### 4.1 Find the table lines

The script reads the published results for the edition. It divides the sum of all song points by 58. It rounds that result to the nearest whole number. The whole number is the number of voters. This number is correct when every voter gives all 58 points. The number of songs is the number of published rows for the edition.

The number of vertical lines is the number of voters plus one. These lines are the side borders of the columns. The number of horizontal lines is the number of songs plus one. These lines are the top and bottom borders of the rows.

The program `grid_lines` looks for gray pixels. A pixel is one colored dot in an image. A pixel is gray when all of these limits are true:

- The red value is more than 55 and less than 210.
- The difference between red and green is less than 45.
- The difference between green and blue is less than 45.

For a vertical line, the program starts at one fifth of the image width. It does this because the song names are on the left. It counts gray pixels on every second row. The rows are in the band from one twelfth to eleven twelfths of the image height. An image column is part of a line when that count is more than 40.

For a horizontal line, the program counts gray pixels on every second column. The count starts at one third of the image width. It stops before 95 percent of the image width. An image row is part of a line when that count is more than 25.

A line can be several adjacent positions. The program keeps the position with the highest count in that group. That count is the strength of the line.

The script then looks for a group of lines with almost equal gaps. In one group, the largest gap minus the smallest gap must be 12 pixels or less. The script can find more than one group. It tries each pair of one vertical group and one horizontal group.

#### Search 1

Search 1 tries the first limit below. If that limit finds no group, search 1 tries the second limit.

Vertical limits for search 1:

1. The gap is from 28 pixels to 55 pixels, and the strength is 90 or more.
2. The gap is from 26 pixels to 60 pixels, and the strength is 70 or more.

Horizontal limits for search 1:

1. The gap is from 26 pixels to 46 pixels, and the strength is 70 or more.
2. The gap is from 24 pixels to 50 pixels, and the strength is 50 or more.

#### Search 2

If no pair from search 1 passes the tests in [section 4.3](#43-make-each-column-the-same-as-the-point-card), the script starts search 2.

- Search 2 keeps a vertical line only when its strength is 60 or more.
- It keeps a horizontal line only when its strength is 50 or more.
- It removes a vertical line when a stronger vertical line is within 16 pixels.
- It removes a horizontal line when a stronger horizontal line is within 12 pixels.
- If two lines are within 2 pixels, the script keeps the earlier line.
- The vertical gap must then be from 28 pixels to 46 pixels.
- The horizontal gap must then be from 26 pixels to 40 pixels.
- In search 2, the largest gap minus the smallest gap must be 12 pixels or less.

### 4.2 Read the point value in each cell

The program `read_grid` copies eight digit shapes from `results_screenshots/STL41.jpg`. The digits are 1, 2, 3, 4, 5, 6, 7, and 8. Each shape is 10 pixels wide and 16 pixels tall. If a template cell is not a single digit, the program stops.

The program then opens the edition screenshot. It leaves a margin inside each table line. The margin is 6 pixels on the left and 6 pixels on the right. The margin is 5 pixels at the top and 4 pixels at the bottom.

A pixel is light ink when red plus green plus blue is more than 400. A pixel is orange when all of these limits are true:

- The red value is more than 175.
- The green value is more than 85.
- The blue value is less than 170.
- Red is more than green plus 25.

The program does the four tests below in order. The first test that gives a value supplies the cell value.

1. If orange ink fills more than one fifth of the cell, the value is 12. The number 12 is orange on the screenshot.
2. If light ink fills less than one fortieth of the cell, the cell is empty.
3. If the light ink is wider than it is tall, the value is 10. Its ink is wide because the number 10 has two digits.
4. For every other cell, the program makes a new shape from the light ink. The new shape is 10 pixels wide and 16 pixels tall. A pixel of the new shape is on when half of that part, or more, is light ink. The program counts the pixels that are not the same as each template shape. The digit with the smallest count is the value.

### 4.3 Make each column the same as the point card

Each column must contain the point card, with each value one time. Each published score pattern comes from the point total and the counts of 12, 10, and 8. The script makes a list of the score patterns of the rows. It makes the same list from the published results. It sorts both lists. It keeps a table only when the two lists are the same. The row order can differ from the order in the published results.

The script can replace a value only when that column has exactly ten cells with a point value. If a column has a different count, the script rejects that table. A replaced value stays in the same cell. The script counts the values that occur too many times. It counts the point values that occur zero times. The two counts must be equal. Each count must be 1, 2, or 3. The script tries each way to put the point values that occur zero times into the extra cells. A column that already has the point card stays unchanged.

The script rejects the table in these cases:

- Two or more changes of one line group give the published score patterns.
- One column has more than 500 possible changes.
- The full table has more than 8000 possible changes.

If several line groups pass these tests, the script keeps one group. It keeps the group whose first row is nearest to the highest song total. A first-row total that is equal to the highest song total is best. If two groups are the same distance from that total, the script keeps the first group. If no group passes, the script shows `grid does not match the results`.

### 4.4 Find the song for each row

The script calculates the score pattern of the row. It finds the published songs that have the same score pattern. If exactly one song has that score pattern, that song is the row.

If two or more songs have that score pattern, the script reads TIE. TIE must have an entry for that row number. The entry gives the country. The script keeps the published song that has that country.

Before the country test, the script makes each published country name simple. Some country names contain a special space character.

1. It changes that special space into a normal space.
2. It changes every letter to lower case.
3. It removes each character with a code of 128 or more. A character code is the number that identifies a character. This step removes flag symbols and accented letters.
4. It makes these name changes:
   - `the netherlands` and `holland` become `netherlands`.
   - `usa` becomes `united states`.
   - `turkiye` becomes `turkey`.

The country text in the ballot file stays in its published form. The script uses the simple form for the TIE test.

The row must match exactly one song. If it does not, the script stops and shows the edition and the row number. The row number in that error starts at 1. Row 1 in the error is row 0 in the TIE list. The ballot file stays unchanged.

### 4.5 Find the voter for each column

A voter gives no points to a song that they entered. Those cells are empty. A voter can have more than one song in the edition. Every one of those songs must be empty in that voter's column. The nicknames come from the NAMES list.

The script uses three tests, in this order.

#### Test 1. Nickname

The script looks for the nickname in ALIAS. If ALIAS has that nickname, the script gets the voter name. Test 1 uses that voter only when the voter has a song in this edition. If all songs from that voter are empty in the column, the column belongs to that voter. The script removes that voter from the voters that remain.

#### Test 2. Confirmed name

The script reads the CONFIRMED list for the edition. This test uses the confirmed name directly. The confirmed voter becomes the voter for that nickname. If test 1 gave this voter to another column, the script clears that other column. If test 1 gave this nickname a different voter, that voter returns to the voters that remain. Test 3 can give a voter to a column that test 2 clears.

#### Test 3. Only one voter remains

The script looks at each column that has no voter. It looks at each voter that has no column. If only one of those voters has all of their songs empty, that voter gets the column. The script repeats this test until a pass gives no column.

If a column still has no voter, the script shows the voters that fit that column. It shows `no entrant fits` when no voter that remains has all of their songs empty. The script prepares ballot rows for the edition only when every column has one voter. Until then, it continues with the next edition.

### 4.6 Prepare the ballot rows

Each cell that has a point value becomes one ballot row. The row has these fields:

- Edition: the contest number.
- Code: STL plus the contest number. For example, `STL39`.
- HOD: the voter.
- Receiving HOD: the Head of Delegation who entered the song.
- Receiving Country: the country text from the published results.
- Points: the point value in the cell.

## 5. Ballot file

The script writes the ballot file when the command contains `--write` and one or more editions passed. That write replaces the whole file. The new file has the editions that passed in this run.

The script sorts the rows by edition number, from low to high. In one edition, it sorts the voter names from A to Z. The sort treats capital letters and lower case letters as the same. For one voter, it puts high point values before low point values.

The file is UTF-8 text. UTF-8 is a way to store letters from English and from other languages. Three bytes at the start mark the file as UTF-8. Each line ends with a carriage return and then a line feed. These marks help a spreadsheet program open the file.

The first line is the header. The header names are Edition, Code, HOD, Receiving HOD, Receiving Country, and Points. Five empty fields follow Points.

This is one vote from edition 28:

| Field | Value |
| --- | --- |
| Edition | 28 |
| Code | STL28 |
| HOD | Alex |
| Receiving HOD | Jana |
| Receiving Country | The Canada text from the published results. The text can contain a flag symbol. |
| Points | 12 |

Alex gave 12 points to the song that Jana entered for Canada.
