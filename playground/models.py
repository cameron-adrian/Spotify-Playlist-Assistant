from django.db import models
from django.urls import reverse

# Create your models here.


# class Playlist(models.Model):
#     """A typical class defining a model, derived from the Model class."""

#     # Fields
#     created_at = models.DateTimeField()
#     # Is this the layer where I'd include a call w/ spotipy
#     playlist_name = models.CharField(
#         max_length=20, help_text='This should be the name of the playlist')
#     # …

#     # Metadata
#     class Meta:
#         ordering = ['-my_field_name']

#     # Methods
#     def get_absolute_url(self):
#         """Returns the URL to access a particular instance of MyModelName."""
#         return reverse('model-detail-view', args=[str(self.id)])

#     def __str__(self):
#         """String for representing the MyModelName object (in Admin site etc.)."""
#         return self.my_field_name
