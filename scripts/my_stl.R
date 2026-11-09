library(tidyverse)
library(ggplot2)
showtext::showtext.auto()

my_stats <- read.csv('my_stats.csv')
spotify_info <- read.csv('ShareTheLove.csv')

exclude <- c('GIMS', 'Mathea', 'The Chainsmokers', 'Alvaro Soler')

df <- my_stats %>% 
  mutate(Song = tolower(Song)) %>%
  left_join(spotify_info %>% mutate(Song = tolower(Song)), by=c('Song')) %>%
  filter(!Artist.y %in% exclude,
         !is.na(Happy))

pca_fit <- df %>% select(Dance, Energy, Acoustic, Instrumental, Happy, Speech, Live, Loud..Db.) %>%
  scale() %>% 
  prcomp() %>%
  broom::augment(df) %>%
  mutate(category = case_when(
    Results == 1 ~ 'winner',
    Results > 1 & Results <= 3 ~ 'top 3',
    Results > 3 & Results <= 5 ~ 'top 5', 
    Results > 5 & Results <= 10 ~ 'top 10',
    TRUE ~ 'others'
  ) %>% factor(levels = c('winner', 'top 3', 'top 5', 'top 10', 'others')))



ggplot(pca_fit, aes(x=.fittedPC1, y=.fittedPC2, color=category)) +
  geom_point() +
  theme_bw(18) +
  ggrepel::geom_text_repel(aes(label=Song)) +
  scale_color_manual(
    values = c('blue', 'orange', 'purple', 'brown', 'gray')
  )

ggplot(pca_fit, aes(x=Edition, y=Results)) +
  geom_point(aes(color=category)) +
  geom_smooth(method='lm') +
  theme_bw(18) +
  scale_color_manual(
    values = c('blue', 'orange', 'purple', 'brown', 'gray')
  )
  


