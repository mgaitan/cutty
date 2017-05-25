from collections import defaultdict
from decimal import Decimal
from itertools import groupby
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from brabbel import Expression
from model_utils import Choices
from . import csp



# Create your models here.
class Brand(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class System(models.Model):
    brand = models.ForeignKey('Brand')
    name = models.CharField(max_length=50)
    price = models.DecimalField(decimal_places=2, max_digits=6)       # by kg
    catalog = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    system = models.ForeignKey('System')
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True, null=True)
    weight = models.DecimalField(decimal_places=3, max_digits=7)
    image = models.ImageField(null=True, blank=True)
    length = models.IntegerField(default=6000)


    def optimize(self, pieces, strategy='GREEDYMATCH'):
        return csp.optimize(list(enumerate(pieces, 1)), strategy=strategy, max_width=self.length)


    def __str__(self):
        return self.code

    class Meta:
        ordering = ['code']


class Cut(models.Model):
    CUTS_TYPE = Choices('45-45', '45-90', '90-90')
    quantity = models.PositiveIntegerField()
    profile = models.ForeignKey('Profile')
    description = models.CharField(max_length=200, blank=True, null=True)
    formula = models.CharField(max_length=50)
    kind = models.CharField(max_length=50, choices=CUTS_TYPE)

    def __str__(self):
        return '{c.quantity} x {c.profile}: {c.formula} ({c.kind})'.format(c=self)

    def clean(self):
        try:
            r = Expression(self.formula).evaluate({'h': 10, 'a': 20})
        except AttributeError:
            raise ValidationError({'formula': _('Not valid formula')})

    def length(self, h, a):
        return Expression(self.formula).evaluate({'h': h, 'a': a})

    def pieces(self, h, a):
        return [self.length(h, a)] * self.quantity


class OpeningKind(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True, null=True)
    dvh = models.BooleanField()
    system = models.ForeignKey('System')
    cuts = models.ManyToManyField('Cut')

    def __str__(self):
        return self.name


class Opening(models.Model):
    width = models.IntegerField()
    height = models.IntegerField()
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True, null=True)
    kind = models.ForeignKey('OpeningKind')
    project = models.ForeignKey('Project', null=True, blank=True, related_name='openings')

    def __str__(self):
        return self.name

    def calculate(self):
        def _get_pieces(cuts):
            pieces = []
            for c in cuts:
                pieces.extend(c.pieces(self.height, self.width))
            return pieces

        cuts = self.kind.cuts.order_by('profile')
        return dict((profile, _get_pieces(_cuts)) for profile, _cuts in groupby(cuts, lambda x: x.profile))



class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


    def calculate(self, strategy='GREEDYMATCH'):
        total_pieces = defaultdict(list)
        for op in self.openings.all():
            for k, v in op.calculate().items():
                total_pieces[k].extend(v)

        total_weight = Decimal('0')
        total_cost = Decimal('0')
        total_waste_weight = 0
        total_waste_cost = Decimal('0')
        total_quantity = 0
        result = {}
        for profile, cuts in total_pieces.items():
            optimization = profile.optimize(cuts, strategy=strategy)
            waste = csp.calc_waste(optimization, max_width=profile.length)
            waste_weight = waste * profile.weight / Decimal('1000.0')
            quantity = len(optimization)
            weight = quantity * profile.weight * profile.length / Decimal('1000.0')
            cost = weight * profile.system.price
            total_weight += weight
            total_quantity += quantity
            total_cost += cost
            total_waste_weight += waste_weight
            total_waste_cost += waste_weight * profile.system.price

            result[profile.code] = {
                'pieces': len(cuts),
                'optimization': optimization,
                'waste': waste,
                'quantity': quantity,
            }
        result['total_weight'] = total_weight
        result['total_quantity'] = total_quantity
        result['total_waste_weight'] = total_waste_weight
        result['total_waste_cost'] = total_waste_cost
        result['total_cost'] = total_cost

        return result