from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from django_date_extensions.fields import ApproximateDate


def test_index(client, future_event, past_event):
    # Access homepage
    resp = client.get(reverse('core:index'))
    assert resp.status_code == 200

    # Check if it returns a list of past and future events
    assert 'past_events' and 'future_events' in resp.context

    # Only the future event is on the list
    event_ids = set(event.pk for event in resp.context['future_events'])
    assert event_ids == {future_event.pk}


def test_event_published(client, future_event, past_event):
    # Check if it's possible to access the page
    url1 = '/' + future_event.page_url + '/'
    resp_1 = client.get(url1)
    assert resp_1.status_code == 200

    # Check if it's possible to access the page
    url2 = '/' + past_event.page_url + '/'
    resp_2 = client.get(url2)
    assert resp_2.status_code == 200

    # Check if website is returning correct data
    assert 'page' and 'menu' and 'content' in resp_1.context
    assert 'page' and 'menu' and 'content' in resp_2.context

    # Check if not public content is not available in context:
    assert future_event.pk not in {content.pk for content in resp_1.context['content']}


def test_event_unpublished(client, hidden_event):
    # Check if accessing unpublished page renders the event_not_live page
    url = '/' + hidden_event.page_url + '/'
    resp = client.get(url)
    assert resp.status_code == 200

    # Check if website is returning correct data
    assert 'city' and 'past' in resp.context


def test_event_unpublished_with_future_and_past_dates(client, no_date_event):
    future_date = timezone.now() + timedelta(days=1)
    past_date = timezone.now() - timedelta(days=1)

    # make the event date in the future
    no_date_event.date = ApproximateDate(
        year=future_date.year, month=future_date.month, day=future_date.day)
    no_date_event.save()

    # Check if accessing unpublished page renders the event_not_live page
    url = '/' + no_date_event.page_url + '/'
    resp = client.get(url)
    assert resp.status_code == 200

    # Check if website is returning correct content
    assert 'will be coming soon' in str(resp.content)

    # make the event date in the past
    no_date_event.date = ApproximateDate(
        year=past_date.year, month=past_date.month, day=past_date.day)
    no_date_event.save()

    # Check if accessing unpublished page renders the event_not_live page
    url = '/' + no_date_event.page_url + '/'
    resp = client.get(url)
    assert resp.status_code == 200

    # Check if website is returning correct content
    assert 'has already happened' in str(resp.content)


def test_event_unpublished_with_authenticated_user(admin_client, hidden_event):
    """ Test that an unpublished page can be accessed when the user is
    authenticated """

    url = '/' + hidden_event.page_url + '/'
    resp = admin_client.get(url)

    assert resp.status_code == 200
    # Check if website is returning correct data
    assert hidden_event.page_title in resp.content.decode('utf-8')


def test_coc(client):
    AVAILABLE_LANG = {
        'en': '<h1>Code of Conduct</h1>',
        'es': '<h1>Código de Conducta</h1>',
        'fr': '<h1>Code de Conduite</h1>',
        'ko': '<h1>준수 사항</h1>',
        'pt-br': '<h1>Código de Conduta</h1>'
    }
    for lang, title in AVAILABLE_LANG.items():
        response = client.get('/coc/{}/'.format(lang))
        assert title in response.content.decode('utf-8'), title


def test_coc_invalid_lang(client):
    response = client.get('/coc/pl/')
    assert response.status_code == 404


def test_coc_redirect(client):
    REDIRECTS = {
        'coc/': '/coc/',
        'coc-es-la/': '/coc/es/',
        'coc-fr/': '/coc/fr/',
        'coc-kr/': '/coc/ko/',
        'coc-pt-br/': '/coc/pt-br/',
        'coc/rec/': '/coc/pt-br/',
    }
    for old_url_name, new_url in REDIRECTS.items():
        old_url = reverse('django.contrib.flatpages.views.flatpage', args=[old_url_name])
        resp = client.get(old_url)
        assert resp.status_code == 301
        assert resp['Location'] == new_url
