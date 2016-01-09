from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
todaystable = Table('todaystable', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=100)),
    Column('phone_number', VARCHAR(length=10)),
    Column('res_latitude', FLOAT),
    Column('res_longitude', FLOAT),
    Column('rider_or_driver', VARCHAR(length=6)),
)

todaystabledrivers = Table('todaystabledrivers', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=100)),
    Column('phone_number', String(length=10)),
    Column('res_latitude', Float),
    Column('res_longitude', Float),
    Column('time_leaving', String(length=4)),
)

todaystableriders = Table('todaystableriders', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', String(length=100)),
    Column('phone_number', String(length=10)),
    Column('res_latitude', Float),
    Column('res_longitude', Float),
    Column('special_requests', String(length=20)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['todaystable'].drop()
    post_meta.tables['todaystabledrivers'].create()
    post_meta.tables['todaystableriders'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['todaystable'].create()
    post_meta.tables['todaystabledrivers'].drop()
    post_meta.tables['todaystableriders'].drop()
